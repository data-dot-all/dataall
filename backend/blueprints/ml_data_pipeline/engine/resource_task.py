""" The file containing functions to create resources defined under aws_resource
    It incluces Glue Connections, SNS topics, ApiGateway, DynamoDB, Lambda Function, Lambda layers, Athena Workgroups and prepared statements.
"""
import ast
import copy
import json
import os
import re
import uuid

import boto3
from aws_cdk import (
    aws_athena,
    aws_batch,
    aws_dynamodb,
    aws_ec2,
    aws_ecr,
    aws_ecs,
    aws_events,
    aws_events_targets,
    aws_glue,
)
from aws_cdk import aws_iam
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_lambda_python as lambda_python
from aws_cdk import aws_s3, aws_sagemaker, aws_sns, aws_sns_subscriptions, aws_ssm, core
from aws_cdk.aws_lambda import Code
from engine.apigateway.apigateway_mapper import ApiGatewayPropsMapper
from engine.dynamodb.dynamodb_mapper import DynamoDBPropsMapper
from engine.lambdafx.lambda_mapper import LambdaFxPropsMapper


class ResourceCreationException(Exception):
    """Exception for resource creation problem."""

    def __init__(self, message, resource_name):
        super().__init__()
        self.message = message
        self.resource_name = resource_name

    def __str__(self):
        return f"{self.message} ({self.resource_name})"


def code_from_path_and_cmd(path: str, cmd: str, compatible_runtime: lambda_.Runtime):
    """Creates an aws_cdk Code given a path and command to bundle.
    Parameters
        path: the path of the asset
        cmd: the bash command to be executed.
    """
    return Code.from_asset(
        path=f"{path}",
        bundling=core.BundlingOptions(
            image=core.BundlingDockerImage.from_registry(f"amazon/aws-sam-cli-build-image-{compatible_runtime.name}"),
            command=["bash", "-c", cmd],
        ),
    )


def update_environments(resource, state_machine_arn, bucket_name, stage, saml_group, stack):
    """Updates environment configuration by including the ARN of state machine."""
    env = copy.deepcopy(resource["config"].get("environment", {}))
    # Add the ARN as one item in environment
    env["PIPELINE_STATE_MACHINE_ARN"] = state_machine_arn
    env["PIPELINE_BUCKET"] = bucket_name
    env["PIPELINE_STAGE"] = stage
    env["SAML_GROUP"] = saml_group

    if stack.commit_id:
        env["CommitID"] = stack.commit_id
    if stack.build_id:
        env["BuildID"] = stack.build_id

    return env


## Resources ##

## SNS Topic##
def make_sns_topic(stack, resource):
    """creation of SNS topics and SNS access policy
    :param stack the englobing stack
    :resource the configuration
    Example:
         - Name: my_sns_topic
           type: sns_topic
           config: #Introduce the SUBSCRIPTION accounts that will have subscribe access to the topic.
            subscriber_accounts: ["2222222222..","111111111111..."]
    By default all services of the codepipeline account have publish and subscribe permission
    Subscriber accounts are an optional parameter to get subscribe access to other accounts
    """
    topic = aws_sns.Topic(
        stack,
        id=f"{resource.get('name')}-SNS",
        topic_name=f"{resource['name']}-{stack.pipeline_name}",
    )
    topic_policy = aws_sns.TopicPolicy(stack, f"{resource.get('name')}-policy", topics=[topic])
    aws_account = stack.accountid
    topic_policy.document.add_statements(
        aws_iam.PolicyStatement(
            actions=["sns:Publish", "sns:Subscribe"],
            principals=[aws_iam.AnyPrincipal()],
            resources=[topic.topic_arn],
            conditions=({"StringEquals": {"AWSSourceOwner": aws_account}}),
        )
    )
    if resource.get("config").get("subscriber_accounts"):
        for account in resource.get("config").get("subscriber_accounts"):
            print(account)
            topic_policy.document.add_statements(
                aws_iam.PolicyStatement(
                    actions=["sns:Subscribe"],
                    principals=[aws_iam.AccountPrincipal(account)],
                    resources=[topic.topic_arn],
                )
            )

    return topic


## Glue Connection ##
def make_glue_connection(stack, resource):
    """
    Creates a Glue Connection.
    :param stack the englobing stack
    :resource the configuration
    Example:
         - Name: redshift_connection
           type: glueconnection
           config:
              subnet_id: subnet-xxx
              security_group_id:
                  - sg-xxx
              jdbc_url: /glueconnection/jdbc_url
              username: /glueconnection/username
              password: /glueconnection/pass
    """
    client = boto3.client("ssm")

    config = resource.get("config", {})

    jdbc_url, jdbc_username, jdbc_pass = client.get_parameters(
        Names=[config.get("jdbc_url"), config.get("username"), config.get("password")],
        WithDecryption=True,
    )

    jdbc_connection = aws_glue.CfnConnection(
        stack,
        id=f"{resource['name']}-GC",
        catalog_id=stack.accountid,
        connection_input=aws_glue.CfnConnection.ConnectionInputProperty(
            name="jdbc_connection",
            connection_type="JDBC",
            physical_connection_requirements=aws_glue.CfnConnection.PhysicalConnectionRequirementsProperty(
                subnet_id=config.get("subnet_id"),
                security_group_id_list=config.get("security_group_id"),
            ),
            connection_properties={
                "JDBC_CONNECTION_URL": jdbc_url,
                "USERNAME": jdbc_username,
                "PASSWORD": jdbc_pass,
            },
        ),
    )
    return jdbc_connection


## Lambda ##
class LambdaRuntimeException(Exception):
    def __init__(self, msg):
        super().__init__()
        self.message = msg

    def __str__(self):
        return self.message


def lambda_to_runtime(config):
    """Gets the runtime for python code.
    Parameter
        config: the configuration of the job/resource
    """

    rt = config["config"].get("runtime", "python3.7").lower()
    if rt == "python3.7":
        return lambda_.Runtime.PYTHON_3_7
    elif rt == "python3.6":
        return lambda_.Runtime.PYTHON_3_6
    elif rt == "python3.8":
        return lambda_.Runtime.PYTHON_3_8
    else:
        raise LambdaRuntimeException("Unsupported lambdafx runtime {}".format(rt))


def default_lambda_description(resource, stack):
    """Returns the default lambdafx description given the job name and pipeline name.
    Parameters
        job: the job definition
        stack: the stack englobing the lambdafx
    """
    return "Python lambdafx created by data.all {} {}".format(resource["name"], stack.pipeline_name)


def make_lambda_layer(
    stack,
    id: str,
    path: str,
    compatible_runtime: lambda_.Runtime,
    cmd: str,
    description: str = None,
):
    """Deploys lambdafx layer given its id, the path of the code, and the compatible runtime. The deployment takes place in a docker container
    compatible for creating the layer. The caller of this function needs to define the command to be executed in the docker container.

    Parameters
        stack: the containing stack
        id: the ID of the layer version stack.
        compatible_runtime: the compatible runtime. Python3_6, Python3_7, or Python3_8.
        cmd: the command to be executed.
        Example of command is :
            rm -rf /asset-output/python  &&
                    pip install -r requirements.txt --target /asset-output/python --quiet &&
                    rm -rf /asset-output/python/scipy* && rm -rf /asset-output/python/numpy*
        description: the description of the lambdafx layer.

    """
    code = code_from_path_and_cmd(path, cmd, compatible_runtime)
    desc = description if description else default_lambda_layer_version_desc()
    return lambda_.LayerVersion(
        stack,
        id,
        compatible_runtimes=[compatible_runtime],
        code=code,
        layer_version_name=id,
        description=desc,
    )


def make_lambda_function_trigger(stack, resource, state_machine_arn, bucket_name, stage, saml_group):
    """Makes python function and its corresponding invocation for a lambdafx function that is used to trigger
    the step function created by the pipeline.
    The lambdafx function that is created is similar to the regular lambdafx, except that the lambdafx function is provided
    with environment variable that includes the state_machine_arn

    Parameters
       stack: the target CDK stack
       resource: the resource configuration
       state_machine_arn: the ARN of the state machine
       bucket_name the name of the pipeline bucket
       stage the stage (test or prod)
    """
    # Add to the existing environment definition in the
    resource["config"]["environment"] = update_environments(
        resource, state_machine_arn, bucket_name, stage, saml_group, stack
    )
    return make_lambda_python_function(stack, resource)


def make_lambda_python_function(stack, resource):
    """Makes lambdafx python function outside the step function.
    Optionally, a cron schedule is associated to the python function.

    Examples:
        aws_resources:
            - name: sfn_trigger
              type: lambdafx
              config:
                scheduler:
                    cron: "cron(0 4 * * ? *)"
                    payload: "{'source_id': 'my_source'}"
                entry: "lambdafx/sfn_trigger"
                index: "handler.py"
                handler: "handler"
                runtime: python3.7
    Parameters
        stack the stack that contains the lambdafx function.
        resource the resource configuration.
    """
    lambda_fn = lambda_python.PythonFunction(
        stack,
        resource["name"],
        runtime=lambda_to_runtime(resource),
        function_name=f"{resource['name']}-{stack.pipeline_name}",
        description=resource.get("description", default_lambda_description(resource, stack)),
        memory_size=resource["config"].get("memory_size", 1028),
        **LambdaFxPropsMapper.map_function_props(stack, resource["name"], resource["config"]),
    )

    # only pipeline_iam_role_arn could access to the lambda
    principal = iam.ArnPrincipal(stack.pipeline_iam_role_arn)

    lambda_fn.add_permission(
        f"TriggerLambdaPermissionBasic{resource['name']}",
        principal=principal,
        action="lambda:*",
    )
    # pipeline_fulldev_iam_role could access to the lambda
    principal = iam.ArnPrincipal(stack.pipeline_fulldev_iam_role)

    lambda_fn.add_permission(
        f"TriggerLambdaPermissionFullDev{resource['name']}",
        principal=principal,
        action="lambda:*",
    )
    # pipeline_admin_iam_role could access to the lambda
    principal = iam.ArnPrincipal(stack.pipeline_admin_iam_role)

    lambda_fn.add_permission(
        f"TriggerLambdaPermissionAdmin{resource['name']}",
        principal=principal,
        action="lambda:*",
    )

    stack.set_resource_tags(lambda_fn)

    # Handles SNS topic as event source if defined:
    if resource["config"].get("sns"):
        if resource["config"].get("sns").get("topic_arn"):
            topic_arn = resource["config"].get("sns").get("topic_arn")
            topic_name = sanitized_name(topic_arn).split(":")[-1]
            print(topic_name)
            topic = aws_sns.Topic.from_topic_arn(
                stack,
                id=f"{resource.get('name')}-{topic_name}",
                topic_arn=resource["config"].get("sns").get("topic_arn"),
            )
            topic.add_subscription(aws_sns_subscriptions.LambdaSubscription(lambda_fn))
        else:
            raise ResourceCreationException("Missing SNS topic in {}".format(resource["name"]), "lambda")

    # Handles scheduling when defined
    rule_name = resource.get("name")
    if resource["config"].get("scheduler"):
        scheduler_config = resource["config"].get("scheduler")
        rules = [target_event_rule(stack, scheduler_config, lambda_fn, None, rule_name)]
    else:
        rules = [
            target_event_rule(stack, scheduler_config, lambda_fn, None, f"{rule_name}_{i}")
            for i, scheduler_config in enumerate(resource["config"].get("schedulers", []))
        ]

    return lambda_fn, rules


def target_event_rule(stack, scheduler_config, lambda_fn, state_fn=None, rule_name="rule"):
    """Creates an Event from cron scheduler definition for lambda function or step function.

    Parameters
        scheduler_config the configuration
        lambda_fn the lambda function corresponding to the schedule
        state_fn the state function corresponding to the schedule
        stack the stack that encloes the lambda function
    """
    # Gets the cron definition
    if scheduler_config.get("cron") and scheduler_config.get("cron").startswith("cron"):
        lambda_schedule = aws_events.Schedule.expression(scheduler_config.get("cron"))
    else:
        raise ResourceCreationException(
            "Invalid cron scheduler {} for lambda".format(str(scheduler_config)),
            "lambda",
        )

    # Gets the payload
    if scheduler_config.get("payload"):
        payload_dic = ast.literal_eval(scheduler_config.get("payload"))
        json_string = json.dumps(payload_dic)
        json_final = json.loads(json_string)

        event_input = aws_events.RuleTargetInput.from_object(json_final)
    else:
        event_input = None

    # Builds the rule
    if lambda_fn:
        event_lambda_target = aws_events_targets.LambdaFunction(handler=lambda_fn, event=event_input)
        return aws_events.Rule(
            stack,
            f"{rule_name}Rule",
            description="Cloudwath Event trigger for Lambda ",
            enabled=True,
            schedule=lambda_schedule,
            targets=[event_lambda_target],
        )

    elif state_fn:
        event_state_fn_target = aws_events_targets.SfnStateMachine(machine=state_fn, input=event_input)
        return aws_events.Rule(
            stack,
            f"{rule_name}Rule",
            description="Cloudwatch Event trigger for State Machine ",
            enabled=True,
            schedule=lambda_schedule,
            targets=[event_state_fn_target],
        )
    else:
        raise Exception("Unexpected parameters, both lambda_fn and state_fn undefined")


def default_lambda_layer_version_desc():
    "Returns default description of layer version." ""
    return "Lambda layer created by dataall"


def make_lambda_layer_version(stack, resource):
    """Makes layer version.
    Parameters
        stack
        resource the configuration of the resource.
    """
    if resource["config"].get("layer_entry"):
        # Creates a new layer version from the definition of a layer
        runtime = lambda_to_runtime(resource)
        if resource["config"].get("bundle_type", "simple") == "simple":
            # A simple layer version. It contains requirements.txt file or files corresponding to a layer.
            plv = lambda_python.PythonLayerVersion(
                stack,
                resource["name"] + "Layer",
                entry=os.path.realpath(resource["config"]["layer_entry"]),
                compatible_runtimes=[runtime],
                description=resource["config"].get("description", default_lambda_layer_version_desc()),
            )
            stack.layer_versions[resource["name"]] = plv
        elif resource["config"].get("bundle_type") == "custom":
            # A layer that needs some post processing (e.g. removal of some files).
            plv = make_lambda_layer(
                stack,
                resource["name"] + "Layer",
                resource["config"]["layer_entry"],
                runtime,
                resource["config"]["cmd"],
                resource["config"].get("description"),
            )
            stack.layer_versions[resource["name"]] = plv
        else:
            raise ResourceCreationException(
                "Unknown bundle_type {}".format(resource["config"].get("bundle_type")),
                "layerversion",
            )

    elif resource["config"].get("layer_arn"):
        # Uses existing layer version
        layer_arn = resource["config"].get("layer_arn")
        lv = lambda_.LayerVersion.from_layer_version_arn(stack, layer_arn["id"], layer_arn["arn"])
        stack.layer_versions[resource["name"]] = lv

    elif resource["config"].get("bucket_arn"):
        runtime = lambda_to_runtime(resource)
        # Uses S3 uploaded layers
        bucket_arn = resource["config"].get("bucket_arn")
        key = resource["config"].get("key")
        lv = lambda_.LayerVersion(
            stack,
            resource["name"] + "-layer",
            compatible_runtimes=[runtime],
            code=lambda_.S3Code(
                bucket=aws_s3.Bucket.from_bucket_arn(stack, resource["name"] + "-bucket", bucket_arn=bucket_arn),
                key=key,
            ),
        )
        stack.layer_versions[resource["name"]] = lv
    else:
        raise ResourceCreationException("Missing layer_entry or layer_arn", "layerversion")


## DynamoDB ##
def make_dynamodb_table(stack, resource):
    """Creates a DynamoDB table.
    Parameters
        stack the staack that englobes the dynamoDB
        resource the configuration of dynamo DB parsed from a configuration file.
    """
    table = aws_dynamodb.Table(
        stack,
        f"dynamodbtable{resource['name']}",
        **DynamoDBPropsMapper.map_props(stack, f"{resource['name']}-{stack.stage}", resource["config"]),
    )

    stack.set_resource_tags(table)

    return table


## Athena ##
def make_athena_workgroup(stack, resource):
    """Creates an Athena workgroup.
    :param stack the englobing stack
    :resource the configuration
    Example:
         - name: dev_workgroup
           type: athena_workgroup
           config:
              query_result_location: "s3://bucketname/prefix/"
    """
    config = resource.get("config", {})
    if config.get("query_result_location"):
        output_location = config.get("query_result_location")
        result_configuration_props = aws_athena.CfnWorkGroup.ResultConfigurationProperty(
            output_location=output_location
        )
    else:
        raise Exception("Missing Athena workgroup output location")

    tags = [core.CfnTag(key=key, value=value) for key, value in stack.resource_tags.items()]

    cfn_workgroup = aws_athena.CfnWorkGroup(
        stack,
        f"athenaworkgroup-{resource['name']}",
        name=f"{resource['name']}",
        description="pipeline workgroup",
        tags=tags,
        work_group_configuration=aws_athena.CfnWorkGroup.WorkGroupConfigurationProperty(
            result_configuration=result_configuration_props
        ),
    )
    return cfn_workgroup


## API Gateway ##
def make_api_gateway(stack, resource):
    """Creates an API Gateway resource
    Parameters
        stack
        resource the resource configuration.
    """
    api_gateway = ApiGatewayPropsMapper.map_props(stack, f"{resource['name']}-{stack.stage}", resource["config"])
    stack.set_resource_tags(api_gateway)
    return api_gateway


def sanitized_name(name):
    return re.sub(r"[^a-zA-Z0-9-]", "", name).lower()


def map_role(stack, batch_name, config_props):
    """Defines the role to be used by the batch job function. The role must be defined under 'role' section
    of config, for example:
    When not defined, the environment role is used.

    Parameters
        stack the pipeline stack
        batch_name the function name to be used to create the role.
        config_props the configuration of the lambda.
    """
    return aws_iam.Role.from_role_arn(
        stack,
        f"{batch_name}Role-{str(uuid.uuid4())[:8]}",
        config_props.get("role", stack.pipeline_iam_role_arn),
        mutable=False,
    )


def make_batch_compute_environment(stack, job):
    compute_env_props = job.get("properties", {})

    if stack.default_vpc_id:
        vpc = aws_ec2.Vpc.from_lookup(stack, "vpc", vpc_id=compute_env_props.get("vpc_id"))
    elif compute_env_props.get("vpc_id"):
        vpc = aws_ec2.Vpc.from_lookup(stack, "vpc", vpc_id=compute_env_props.get("vpc_id"))
    elif compute_env_props.get("vpc_from_cloudformation"):
        vpc = aws_ec2.Vpc.from_vpc_attributes(
            stack,
            "batchvpc",
            availability_zones=stack.availability_zones,
            vpc_id=core.Fn.import_value(compute_env_props.get("vpc_from_cloudformation")),
        )
    else:
        raise Exception("No VPC Information provided")

    if compute_env_props.get("subnet_id"):
        subnets = [
            aws_ec2.Subnet.from_subnet_id(stack, id=f"subnet{i}", subnet_id=subnet_id)
            for i, subnet_id in enumerate(compute_env_props.get("subnet_id"))
        ]
    elif compute_env_props.get("subnet_from_cloudformation"):
        subnet_ids = core.Token.as_list(
            core.Fn.split(
                ",",
                core.Fn.import_value(compute_env_props.get("subnet_from_cloudformation")),
            )
        )
        subnets = [
            aws_ec2.Subnet.from_subnet_attributes(stack, "batchsubnet{}".format(index), subnet_id=subnet)
            for index, subnet in enumerate(subnet_ids)
        ]
    else:
        raise Exception("No Subnets are defined")

    if compute_env_props.get("security_group_id"):
        security_groups = [
            aws_ec2.SecurityGroup.from_security_group_id(stack, id=f"sg{i}", security_group_id=sg_id, mutable=False)
            for i, sg_id in enumerate(compute_env_props.get("security_group_id"))
        ]
    else:
        security_groups = [aws_ec2.SecurityGroup(stack, "BatchSecurityGroup", vpc=vpc, allow_all_outbound=True)]

    instance_types = [aws_ec2.InstanceType(itype) for itype in compute_env_props.get("instance_types", ["optimal"])]

    compute_resource_type_str = compute_env_props.get("compute_resource_type", "ON_DEMAND")
    compute_resource_type = aws_batch.ComputeResourceType[compute_resource_type_str]

    allocation_strategy_str = compute_env_props.get("allocation_strategy", "BEST_FIT")
    allocation_strategy = aws_batch.AllocationStrategy[allocation_strategy_str]

    if compute_resource_type == aws_batch.ComputeResourceType.SPOT:
        bid_percentage = compute_env_props.get("bid_percentage", 100)
    else:
        bid_percentage = None

    launch_template = None
    if "launch_template" in compute_env_props:
        launch_template_props = compute_env_props.get("launch_template")
        launch_template_name = launch_template_props.get("name")
        version = launch_template_props.get("version")
        launch_template = aws_batch.LaunchTemplateSpecification(launch_template_name, version)

    if "instance_role" in compute_env_props:
        instance_role = compute_env_props["instance_role"]
    else:
        instance_role = stack.batch_instance_role

    if ("spot_fleet_role" in compute_env_props) and (compute_resource_type == aws_batch.ComputeResourceType.SPOT):
        spot_fleet_role = aws_iam.Role.from_role_arn(stack, "spotfleetrole", compute_env_props["spot_fleet_role"])
    else:
        spot_fleet_role = None

    tags = copy.deepcopy(stack.resource_tags)
    tags["ce_name"] = job.get("name", "noname")

    compute_resources = aws_batch.ComputeResources(
        vpc=vpc,
        type=compute_resource_type,
        launch_template=launch_template,
        bid_percentage=bid_percentage,
        instance_types=instance_types,
        allocation_strategy=allocation_strategy,
        placement_group=compute_env_props.get("placement_group"),
        maxv_cpus=compute_env_props.get("max_vcpus", 16),
        vpc_subnets=aws_ec2.SubnetSelection(subnets=subnets),
        desiredv_cpus=compute_env_props.get("desired_vcpus", 0),
        minv_cpus=compute_env_props.get("min_vcpus", 0),
        security_groups=security_groups,
        compute_resources_tags=tags,
        instance_role=instance_role,
        spot_fleet_role=spot_fleet_role,
    )
    rnd = str(uuid.uuid4())[:4]

    ce = aws_batch.ComputeEnvironment(
        stack,
        id="dhce-{}-{}".format(job.get("name", "noname"), rnd),
        compute_environment_name="dhce-{}-{}".format(job.get("name", "noname"), rnd),
        compute_resources=compute_resources,
        managed=True,
    )
    ce.apply_removal_policy(core.RemovalPolicy.DESTROY)

    if "name" in job:
        client = boto3.client("ssm")
        parameter_name = f"/{stack.pipeline_name_origin}/{stack.stage}/compute_environment/{job.get('name')}"
        try:
            client.get_parameter(Name=parameter_name)
        except:
            param = aws_ssm.StringParameter(
                stack,
                f"ce{job['name']}",
                parameter_name=parameter_name,
                string_value=ce.compute_environment_arn,
            )
            param.apply_removal_policy(core.RemovalPolicy.DESTROY)
            param.grant_read(aws_iam.ArnPrincipal(stack.pipeline_iam_role_arn))
            param.grant_read(aws_iam.ArnPrincipal(stack.pipeline_fulldev_iam_role))
            param.grant_read(aws_iam.ArnPrincipal(stack.pipeline_admin_iam_role))
    return ce


def make_batch_job_definition(stack, job):
    """Deploys batch job from the properties. By default, the job will run using environment role.
    :param stack the pipeline stack
    :job the configuration from config.yaml
    """
    job_definition_name = f"job-{sanitized_name(job['name'])}"
    job_definition = job.get("job_definition")

    container_properties = job_definition.get("container_properties")
    image = container_properties.get("image")

    image_obj = None
    if image.get("assets"):
        directory = image["assets"].get("directory")
        if not directory:
            raise Exception("Directory is missing")

        build_args = image["assets"].get("build_args")
        file = image["assets"].get("file", "Dockerfile")
        target = image["assets"].get("target")

        image_obj = aws_ecs.ContainerImage.from_asset(
            directory=directory,
            build_args=build_args,
            file=file,
            target=target,
            repository_name=stack.ecr_repository_uri,
        )

    elif image.get("ecr_repository"):

        repository = aws_ecr.Repository.from_repository_arn(
            stack,
            f"repository{job_definition_name}",
            image["ecr_repository"].get("arn", stack.ecr_repository_arn),
        )
        tag = image["ecr_repository"].get("tag")
        image_obj = aws_ecs.ContainerImage.from_ecr_repository(repository, tag=tag)

    elif image.get("repository_name"):
        image_obj = aws_ecs.ContainerImage.from_registry(image["repository_name"])

    else:
        raise Exception("Missing container image information")

    retry_attempts = job_definition.get("retry_attempts", 10)

    gpu_count = container_properties.get("gpu_count")

    if container_properties.get("instance_type"):
        instance_type = aws_ec2.InstanceType(container_properties.get("instance_type"))
    else:
        instance_type = None

    if container_properties.get("linux_parameters"):
        shared_memory_size = container_properties["linux_parameters"].get("shared_memory_size")
        init_process_enabled = container_properties["linux_parameters"].get("init_process_enabled", False)
        linux_parameters = aws_ecs.LinuxParameters(
            stack,
            id="linuxparam" + job_definition_name,
            init_process_enabled=init_process_enabled,
            shared_memory_size=shared_memory_size,
        )
    else:
        linux_parameters = None

    job_definition_obj = aws_batch.JobDefinition(
        stack,
        id=f"{job_definition_name}-{str(uuid.uuid4())[:4]}",
        job_definition_name=f"{job_definition_name}-{stack.stage}-{str(uuid.uuid4())[:4]}",
        retry_attempts=retry_attempts,
        container=aws_batch.JobDefinitionContainer(
            image=image_obj,
            gpu_count=gpu_count,
            instance_type=instance_type,
            linux_params=linux_parameters,
            command=job_definition.get("command"),
            environment=job_definition.get("environment"),
            job_role=map_role(stack, job_definition_name, job),
            memory_limit_mib=job_definition.get("memory_limit_mib", 512),
            vcpus=job_definition.get("vcpus", 1),
        ),
    )

    client = boto3.client("ssm")
    parameter_name = f"/{stack.pipeline_name_origin}/{stack.stage}/job_definition/{job_definition_name}"
    try:
        client.get_parameter(Name=parameter_name)
    except:
        param = aws_ssm.StringParameter(
            stack,
            f"jobdefinition{stack.pipeline_name_origin}",
            parameter_name=parameter_name,
            string_value=job_definition_obj.job_definition_arn,
        )
        param.apply_removal_policy(core.RemovalPolicy.DESTROY)
        param.grant_read(map_role(stack, job_definition_name, job))
    return job_definition_obj


def make_batch_job_queue(stack, resource):
    """Creates a batch job queue.
    Example:
        name: my_job_queue
        priority: 5
    """
    props = resource.get("properties")
    compute_env_props = props.get("computation_environment") or props.get("compute_environment")

    if compute_env_props.get("arn"):
        compute_environments = [
            aws_batch.ComputeEnvironment.from_compute_environment_arn(stack, "cefromarn", compute_env_props.get("arn"))
        ]
    elif compute_env_props.get("arn_params"):

        compute_environments = [
            aws_batch.ComputeEnvironment.from_compute_environment_arn(
                stack,
                "cefromarn" + str(i),
                boto3.client("ssm").get_parameter(Name=arn_param)["Parameter"]["Value"],
            )
            for i, arn_param in enumerate(compute_env_props.get("arn_params"))
        ]

    elif compute_env_props.get("arns"):
        compute_environments = [
            aws_batch.ComputeEnvironment.from_compute_environment_arn(stack, "cefromarn" + str(i), arn)
            for i, arn in enumerate(compute_env_props.get("arns"))
        ]

    elif compute_env_props.get("compute_environment_ref"):
        compute_environments = [
            stack.resources.get(ce_ref) for ce_ref in compute_env_props.get("compute_environment_ref")
        ]

    else:
        compute_environments = [make_batch_compute_environment(stack, {"properties": compute_env_props})]

    job_queue_compute_environments = [
        aws_batch.JobQueueComputeEnvironment(order=i + 1, compute_environment=ce)
        for i, ce in enumerate(compute_environments)
    ]
    rnd = str(uuid.uuid4())[:4]
    job_queue = aws_batch.JobQueue(
        stack,
        f"q-{resource['name']}-{rnd}",
        job_queue_name=f"dh-jobqueue-{resource['name']}-{rnd}",
        priority=resource.get("priority", 1),
        compute_environments=job_queue_compute_environments,
    )

    client = boto3.client("ssm")
    parameter_name = f"/{stack.pipeline_name_origin}/{stack.stage}/job_queue/{resource['name']}"
    try:
        client.get_parameter(Name=parameter_name)
    except:
        param = aws_ssm.StringParameter(
            stack,
            f"jobqueue-param",
            parameter_name=parameter_name,
            string_value=job_queue.job_queue_arn,
        )
        param.apply_removal_policy(core.RemovalPolicy.DESTROY)
        param.grant_read(map_role(stack, resource["name"], resource))

    return job_queue


def make_sagemaker_model_package_group(stack, resource):
    """Create sagemaker model package group.
    :param stack the pipeline stack
    :resource the properties to be used. Only description can be optionally defined, in addition to the name.
    """
    rnd = str(uuid.uuid4())[:4]
    mpg = aws_sagemaker.CfnModelPackageGroup(
        stack,
        f"{resource['name']}-{rnd}",
        model_package_group_name=resource["name"],
        model_package_group_description=resource.get("description"),
    )
    mpg.apply_removal_policy(core.RemovalPolicy.DESTROY)
