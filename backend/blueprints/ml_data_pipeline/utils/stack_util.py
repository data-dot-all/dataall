"""
Helper file to Pipeline stack operations: creation of triggers and resources in resources of the config_dpc.yaml.
resources are defined in engine/resource_task.py
"""
import uuid

import boto3
from .task_group_reader import Stages
import ast
import json
from engine import (
    make_api_gateway,
    make_dynamodb_table,
    make_lambda_layer_version,
    make_lambda_python_function,
    make_lambda_function_trigger,
    make_athena_workgroup,
    make_athena_prepared_statement,
    make_sns_topic,
    make_batch_job_queue,
    make_batch_job_definition,
    make_batch_compute_environment,
    make_sagemaker_model_package_group,
)
from aws_cdk import aws_events, aws_events_targets, core
import re


class ResourceCreationException(Exception):
    """Exception for resource creation problem."""

    def __init__(self, message, resource_name):
        super().__init__()
        self.message = message
        self.resource_name = resource_name

    def __str__(self):
        return f'{self.message} ({self.resource_name})'


class PipelineStackException(Exception):
    def __init__(self, message):
        super().__init__()
        self.message = f'Failed to create pipeline due to {message}'

    def __str__(self):
        return self.message


## General methods
def get_parameter_value(param_name):
    """Gets parameter from parameter store.
    Parameters
        param_name: parameter to be obtained from the parameter store.
    """
    param_value = boto3.client('ssm').get_parameter(Name=param_name)['Parameter'][
        'Value'
    ]
    return param_value


def attr_from_env_paramstore(stack, param_name, param_store_path, dictionary):
    """Resolve attribute from environment variables or from parameter store."""
    return dictionary.get(param_name) or get_parameter_value(
        f'/{stack.pipeline_name_origin}/{stack.stage}/{param_store_path}'
    )


def build_object_attributes(stack, dictionary, pipeline):
    """Builds object attributes from a dictionary or parameter store.
    Parameter
        dictionary: the dictionary
        pipeline: configuration of the pipeline.
    """
    # Pipeline names: with and without the stage information.
    stack.pipeline_name_origin = dictionary.get(
        'ORIGIN_PIPELINE_NAME', pipeline.definition.get('name')
    )
    stack.pipeline_name = dictionary.get(
        'PIPELINE_NAME', pipeline.definition.get('name')
    )

    # Glue job directory.
    stack.jobdir = pipeline.definition.get('jobdir', 'glue_jobs')

    # Pipeline stage. Value examples: TEST, DEV, INT, PROD.The value is not imposed.
    stack.stage = dictionary.get('STAGE', Stages.TEST)

    # Bucket of the pipeline. It consists of files required for runtime of the pipeline.
    stack.bucket_name = attr_from_env_paramstore(
        stack, 'BUCKET_NAME', 'bucket_name', dictionary
    )

    # The account ID where the pipeline is defined.
    stack.accountid = attr_from_env_paramstore(
        stack, 'AWSACCOUNTID', 'accountid', dictionary
    )

    # The repository URI where the docker images corresponding to this pipeline is stored.
    stack.ecr_repository_uri = attr_from_env_paramstore(
        stack, 'ECR_REPOSITORY', 'ecr_repository_uri', dictionary
    )

    # The default role of the pipeline.
    stack.pipeline_iam_role_arn = attr_from_env_paramstore(
        stack, 'ENVROLEARN', 'pipeline_iam_role_arn', dictionary
    )

    # All IAM roles of the pipeline admin group
    # e.g if the pipeline admin group is admin in the environment = admin, fulldev and basicdev
    # e.g if the pipeline admin group is fulldev in the environment = fulldev and basicdev
    # e.g the pipeline admin group is admin in the environment = basicdev
    stack.pipeline_fulldev_iam_role = attr_from_env_paramstore(
        stack, 'FULLDEVROLEARN', 'fulldev_iam_role', dictionary
    )

    stack.pipeline_admin_iam_role = attr_from_env_paramstore(
        stack, 'ADMINROLEARN', 'admin_iam_role', dictionary
    )

    # The region in which the pipeline runs
    stack.pipeline_region = attr_from_env_paramstore(
        stack, 'AWS_DEFAULT_REGION', 'pipeline_region', dictionary
    )
    stack.ecr_repository_arn = f'arn:aws:ecr:{stack.pipeline_region}:{stack.accountid}:{stack.ecr_repository_uri}'

    # The build id
    stack.commit_id = dictionary.get('CODEBUILD_RESOLVED_SOURCE_VERSION', '')
    stack.build_id = dictionary.get('CODEBUILD_BUILD_ID', '')
    stack.saml_group = dictionary.get('SAML_GROUP', '')
    stack.batch_instance_role = dictionary.get('BATCH_INSTANCE_ROLE', '')

    stack.pipeline_uri = dictionary.get('PIPELINE_URI')
    stack.environment_uri = dictionary.get('ENVIRONMENT_URI')
    stack.staged_environment_uri = dictionary.get('STAGED_ENVIRONMENT_URI')

    # default vpc_id
    stack.default_vpc_id = dictionary.get('DEFAULT_VPC_ID')


## Triggers
def create_step_function_triggers(stack, pipeline_definition, state_machine_arn):
    """Create all lambdafx functions that may trigger the pipeline.
    It processes the 'triggers' block of the pipeline configuration.

    Example
      triggers:
            - name: prediction_trigger
              type: lambda_function
              description: "The lambdafx that triggers the step function"
              config:
                scheduler:
                    cron: "cron(0 4 * * ? *)"
                    payload: "{ 'plant_id': ['omansur'] }"
                entry: "lambdafx/sfn_trigger"
                index: "handler.py"
                handler: "handler"
    """
    if not pipeline_definition.get('triggers'):
        print('No triggers to create')
        return

    # Sanity checks
    for r in pipeline_definition.get('triggers'):
        if not r.get('name'):
            raise PipelineStackException('missing name for resource {}', str(r))
        if r.get('type') not in {
            'lambda_function'
        }:  # we only support lambdafx as trigger at the moment
            raise PipelineStackException('Unknown type {}'.format(r.get('type')))

    # Create the lambdafx function, just like the usual lambdafx python function
    trigger_names = []  # You can invoke the first trigger from data.all
    for trigger in pipeline_definition.get('triggers'):
        if trigger['type'] == 'lambda_function':
            (lambda_fn, rules) = make_lambda_function_trigger(
                stack,
                trigger,
                state_machine_arn,
                stack.bucket_name,
                stack.stage,
                stack.saml_group,
            )

            stack.resources[trigger.get('name')] = (lambda_fn, rules)

            trigger_name = re.sub(r'[^a-zA-Z0-9-:]', '', trigger.get('name'))

            core.CfnOutput(
                stack,
                f'TriggerFunctionName{trigger_name}',
                export_name=f'{stack.pipeline_uri}-TriggerFunctionName-{trigger_name}-{str(uuid.uuid4())[:8]}',
                value=lambda_fn.function_name,
                description=f'Trigger function name of {stack.pipeline_uri}/{stack.pipeline_name}',
            )
            core.CfnOutput(
                stack,
                f'TriggerFunctionArn{trigger_name}',
                export_name=f'{stack.pipeline_uri}-TriggerFunctionArn-{trigger_name}-{str(uuid.uuid4())[:8]}',
                value=lambda_fn.function_arn,
                description=f'Trigger function ARN of {stack.pipeline_uri}/{stack.pipeline_name}',
            )
            trigger_names.append(trigger_name)

    core.CfnOutput(
        stack,
        f'TriggerFunctionNames',
        export_name=f'{stack.pipeline_uri}-TriggerFunctionNames-{str(uuid.uuid4())[:8]}',
        value=':'.join(trigger_names),
        description=f'List of trigger names separated by colon of {stack.pipeline_uri}/{stack.pipeline_name}',
    )


## Scheduler
def create_event_rule_for_scheduler(
    stack, scheduler_config, lambda_fn, state_fn=None, rule_name='rule'
):
    """Creates an Event from cron scheduler definition for lambdafx function or step function.

    Parameters
        scheduler_config the configuration
        lambda_fn the lambdafx function corresponding to the schedule
        state_fn the state function corresponding to the schedule
        stack the stack that encloes the lambdafx function
    """
    # Gets the cron definition
    if scheduler_config.get('cron'):
        lambda_schedule = aws_events.Schedule.expression(scheduler_config.get('cron'))
    else:
        raise ResourceCreationException(
            'Unknown scheduler {}'.format(str(scheduler_config)), 'lambdafx'
        )

    # Gets the payload
    if scheduler_config.get('payload'):
        payload_dic = ast.literal_eval(scheduler_config.get('payload'))
        json_string = json.dumps(payload_dic)
        json_final = json.loads(json_string)

        event_input = aws_events.RuleTargetInput.from_object(json_final)
    else:
        event_input = None

    # Builds the rule
    if lambda_fn:
        event_lambda_target = aws_events_targets.LambdaFunction(
            handler=lambda_fn, event=event_input
        )
        return aws_events.Rule(
            stack,
            f'{rule_name}Rule',
            description='Cloudwath Event trigger for Lambda ',
            enabled=True,
            schedule=lambda_schedule,
            targets=[event_lambda_target],
        )

    elif state_fn:
        event_state_fn_target = aws_events_targets.SfnStateMachine(
            machine=state_fn, input=event_input
        )
        return aws_events.Rule(
            stack,
            f'{rule_name}Rule',
            description='Cloudwath Event trigger for State Machine ',
            enabled=True,
            schedule=lambda_schedule,
            targets=[event_state_fn_target],
        )
    else:
        raise Exception('Unexpected parameters, both lambda_fn and state_fn undefined')


def create_step_function_scheduler(stack, pipeline_definition, sfn):
    """Schedules step function using the schedulers part of properties of the step function.
    Parameters
        pipeline_definition: the configuration of pipeline
        sfn: the step function to schedule.
    """
    rule_name = stack.pipeline_name
    if pipeline_definition.get('properties', {}).get('scheduler'):
        scheduler_config = pipeline_definition['config'].get('scheduler')
        rules = [
            create_event_rule_for_scheduler(
                stack, scheduler_config, None, sfn, rule_name
            )
        ]
    else:
        rules = [
            create_event_rule_for_scheduler(
                stack, scheduler_config, None, sfn, f'{rule_name}_{i}'
            )
            for i, scheduler_config in enumerate(
                pipeline_definition.get('properties', {}).get('schedulers', [])
            )
        ]
        print('Length of rules {}'.format(len(rules)))

    return rules


## Resources
def create_aws_resources(stack, pipeline):
    """Make one of the aws_resource supported by data.all.
    The resources supported by data.all are:
        - dynamodb for DynamoDB table
        - apigateway for APIGateway
        - sns_topic for SNS topic
        - athena_workgroup for Athena Workgroups
        - athena_prepared_statement for prepared SQL statements
        - lambda_layer for Lambda layer
        - lambda_function for a lambdafx function outside the main step function of the pipeline.
    Parameter
        pipeline: the parsed pipeline configuration.
    """

    if 'aws_resources' not in pipeline.definition:
        print('no AWS resources to be deployed')
        return

    # Sanity checks of aws_resources configuration
    for r in pipeline.definition.get('aws_resources', []):
        if 'name' not in r:
            raise PipelineStackException('missing name for resource {}', str(r))
        if r.get('type') not in {
            'dynamodb',
            'apigateway',
            'lambda_layer',
            'lambda_function',
            'athena_workgroup',
            'sns_topic',
            'athena_prepared_statement',
            'batch_job_definition',
            'batch_compute_environment',
            'batch_job_queue',
            'sagemaker_model_package_group',
        }:
            raise PipelineStackException('Unknown type {}'.format(r.get('type')))

    for resource in pipeline.definition.get('aws_resources', []):
        if resource['type'] == 'dynamodb':
            stack.resources[resource.get('name')] = make_dynamodb_table(stack, resource)
        elif resource['type'] == 'apigateway':
            stack.resources[resource.get('name')] = make_api_gateway(stack, resource)
        elif resource['type'] == 'lambda_layer':
            stack.resources[resource.get('name')] = make_lambda_layer_version(
                stack, resource
            )
        elif resource['type'] == 'lambda_function':
            stack.resources[resource.get('name')] = make_lambda_python_function(
                stack, resource
            )
        elif resource['type'] == 'athena_workgroup':
            stack.resources[resource.get('name')] = make_athena_workgroup(
                stack, resource
            )
        elif resource['type'] == 'athena_prepared_statement':
            stack.resources[resource.get('name')] = make_athena_prepared_statement(
                stack, resource
            )
        elif resource['type'] == 'sns_topic':
            stack.resources[resource.get('name')] = make_sns_topic(stack, resource)
        elif resource['type'] == 'batch_job_definition':
            stack.resources[resource.get('name')] = make_batch_job_definition(
                stack, resource
            )
        elif resource['type'] == 'batch_job_queue':
            stack.resources[resource.get('name')] = make_batch_job_queue(
                stack, resource
            )
        elif resource['type'] == 'batch_compute_environment':
            stack.resources[resource.get('name')] = make_batch_compute_environment(
                stack, resource
            )
        elif resource['type'] == 'sagemaker_model_package_group':
            stack.resources[resource.get('name')] = make_sagemaker_model_package_group(
                stack, resource
            )
        else:
            print('Discarding resource type {}'.format(resource['type']))


def create_resource_tags(stack, dictionary):
    """Tags resources using the value in ENVTAG_ environment variables.

    For example:
        Environment Variables:
            ENVTAG_Application : data.all
            ENVTAG_Owner : owner@amazon.com
        Will make all the created resources to be tagged
            Application: data.all
            Owner: owner@email.com
    """
    tags = dict(
        [
            (k[len('ENVTAG_') :], v)
            for k, v in dictionary.items()
            if k.startswith('ENVTAG_')
        ]
    )

    tags['Application'] = 'data.all'
    tags['PipelineInfo'] = f'{stack.stage}/{stack.pipeline_name_origin}'
    if stack.build_id:
        tags['BuildID'] = stack.build_id
    if stack.commit_id:
        tags['CommitID'] = stack.commit_id
    if stack.pipeline_iam_role_arn:
        tags['EnvironmentRole'] = stack.pipeline_iam_role_arn
    if stack.saml_group:
        tags['samlgroup'] = stack.saml_group.lower()
    tags['PipelineURI'] = stack.pipeline_uri
    tags['EnvironmentURI'] = stack.environment_uri
    return tags
