"""
Class that creates a CDK Stack from a configuration file config_dpc.yaml
The configuration file consists of three blocks:
      1. Metadata of the stack creation. Consists of name and description of the stack creation.
      2. aws_resources block where the resources definition are to be deployed and defined.
      3. pipeline blocks that define set of pipelines to be created. When there is only one pipeline, the
         definition can go directly to groups which defines the pipeline.

 The class has the following attributes:
    - pipelines the names of the pipelines.
    - stage the stage of the pipeline, for example, DEV or PROD
    - bucket_name the S3 bucket where the information needed by the pipelines are stored.
    - accountid the AWS account ID that runs as the context of the execution
    - ecr_repository_uri the repository URI used to store docker images used by sagemaker processing or sagemaker training
    - pipeline_iam_role_arn the environment role
    - pipeline_region the region where the pipeline is to be executed
    - layer_versions all lambdafx layer versions created by the stack
"""
import os

from aws_cdk import aws_iam as iam
from aws_cdk import aws_stepfunctions as stepfunctions
from aws_cdk import core
from aws_cdk import aws_ssm

from utils import stack_util
from utils import stack_task_util


class DataPipeline(core.Stack):
    """Pipeline stack. It creates a list of resources such as dynamoDB tables, API Gateway, standalone lambdafx functions,
    and lambdafx layers.
    """

    def __init__(self, scope, id, pipeline, **kwargs):
        account = os.environ.get("AWSACCOUNTID")
        super().__init__(
            scope,
            id,
            env=core.Environment(account=account, region=os.environ.get("AWS_DEFAULT_REGION")),
            **kwargs,
        )

        # build object attributes from environment variables or parameters store.
        self.build_object_attributes(pipeline)

        # Tracking all layer versions created in the stack.
        self.layer_versions = {}

        # Tracking all resources created under aws_resources block
        self.resource_tags = self.create_resource_tags()
        self.resources = {}

        # The state machines created under groups block
        self.state_machine = None
        self.state_machine_definition = None

        # create resources from aws_resources block of configuration file.
        self.create_aws_resources(pipeline)

        # Creates a step function corresponding to the configuration defined in the configuration file.
        self.create_step_function(pipeline=pipeline)

        for key, value in self.resource_tags.items():
            core.Tags.of(self).add(key, value)

    # Imported stack util methods:

    def build_object_attributes(self, pipeline):
        """Builds object attributes from environment variables or parameter store.
        Parameter
            pipeline: configuration of the pipeline.
        """
        stack_util.build_object_attributes(self, os.environ, pipeline)

    # Scheduler
    def create_step_function_scheduler(self, pipeline_definition, sfn):
        return stack_util.create_step_function_scheduler(self, pipeline_definition, sfn)

    # Triggers
    def create_step_function_triggers(self, pipeline, state_machine_arn):
        """Creates step function triggers"""
        return stack_util.create_step_function_triggers(self, pipeline.definition, state_machine_arn)

    # Resources
    def create_aws_resources(self, pipeline):
        """Make one of the aws_resource supported by data.all.
        The resources supported by data.all are:
            - dynamodb for DynamoDB table
            - apigateway for APIGateway
            - athena_workgroup for Athena Workgroups
            - athena_prepared_statement for Athena SQL Prepared statements
            - sns_topic for SNS topics
            - lambda_layer for Lambda layer
            - lambda_function for a lambdafx function outside the main step function of the pipeline.
        Parameter
            pipeline: the parsed pipeline configuration.
        """
        stack_util.create_aws_resources(self, pipeline)

    def create_resource_tags(self):
        """Tags resources using the value in ENVTAG_ environment variables.

        For example:
            Environment Variables:
                ENVTAG_Application : dataall
                ENVTAG_Owner : owner@email.com
            Will make all the created resources to be tagged
                Application: dataall
                Owner: owner@amazon.com
        """
        return stack_util.create_resource_tags(self, os.environ)

    # Imported Stack task util methods

    def make_step_function_task(self, job, group_index=-1, job_index=-1):
        """Make a task of step functions.
        It can be either
            - glue_job, for glue job
            - athena_query, for athena query
            - sns_publish, for SNS publish task
            - lambda_function, for creation of lambdafx function
            - sagemaker_training, for Sage maker training
            - sagemaker_hpo, for hyperparameter optimization using sagemaker
            - sagemaker_processing, for sagemaker processing
            - sagemaker_batch_transform, for sagemaker batch transform job
            - sagemaker_model, for creation of a sage maker model
            - sagemaker_endpoint_config, for creation of an endpoint configuration
            - sagemaker_endpoint, for creation of end point
            - choice, for a simple, typically runtime branching.
        Parameters
            job: the configuration of the job.
        """
        return stack_task_util.make_step_function_task(self, job, group_index, job_index)

    def build_sagemaker_training_processing_job_image(self, groups):
        """Builds sagemaker processing job images.
        The build only happens when the there are glue_jobs whose job type is either processing or training.

        Parameters
            groups: the definition of the groups from configuration file.
        """
        return stack_task_util.build_sagemaker_training_processing_job_image(self, groups)

    def create_glue_job_names_with_execution_id(self, pipeline, job_names):
        """Creates the glue jobs with execution ID
        Parameters
            pipeline: pipeline configured in config_dpc.yaml
            job_names: names of the jobs defined in the config_dpc.yaml
        """
        return stack_task_util.create_glue_job_names_with_execution_id(self, pipeline, job_names)

    # Local methods
    def set_resource_tags(self, resource):
        """Puts the tag to the resource"""
        for key, value in self.resource_tags.items():
            core.Tags.of(resource).add(key, value)

    def create_step_function(self, pipeline):
        """Creates a step function based on the definition under groups block in configuration file.

        Parameters
           pipeline: parsed configuration file
        """

        # Check if there is any step function to build.
        if not pipeline.definition.get("groups"):
            print("No step functions to build.")
            return

        # Sanity check of job types.
        for group in pipeline.definition.get("groups"):
            for job in group.get("jobs"):
                if not job.get("name"):
                    raise stack_task_util.PipelineTaskException("Missing name for job {}".format(str(job)))
                if job.get("type") not in {
                    "glue_job",
                    "sagemaker_training",
                    "sagemaker_hpo",
                    "sagemaker_processing",
                    "sagemaker_model",
                    "sagemaker_batch_transform",
                    "sagemaker_endpoint_config",
                    "sagemaker_endpoint",
                    "lambda_function",
                    "choice",
                    "athena_query",
                    "sns_publish",
                    "batch",
                }:
                    raise stack_task_util.PipelineTaskException("Unknown job type {}".format(job.get("type")))

        # Builds sagemaker job images for sagemaker_processing or sagemaker_training.
        self.build_sagemaker_training_processing_job_image(pipeline.definition["groups"])

        # Create Glue job names with execution id if there are glue_jobs
        job_names = []
        job_name_generator_task = self.create_glue_job_names_with_execution_id(pipeline, job_names)

        # Make sequence of parallels from groups.
        definition, _, _ = stack_task_util.build_step_function_definition(
            self, pipeline.definition, job_name_generator_task, True
        )

        # Check for presence of global retry/catch.
        # Create parallel container if relevant and add failure chain on catch
        retry_definition = pipeline.definition.get("retry", None)
        catch_definition = pipeline.definition.get("catch", None)
        if retry_definition is not None or catch_definition is not None:
            definition = definition.to_single_state("RetryAndErrorHandler")
            if retry_definition is not None:
                definition = definition.add_retry(
                    backoff_rate=retry_definition.get("backoff_rate", 2),
                    errors=retry_definition.get("error_equals", ["States.ALL"]),
                    interval=core.Duration.seconds(retry_definition.get("interval_seconds", 1)),
                    max_attempts=retry_definition.get("retry_attempts", 3),
                )
            if catch_definition is not None:
                catch_chain, _, _ = stack_task_util.build_step_function_definition(self, catch_definition, None, False)
                definition = definition.add_catch(
                    catch_chain,
                    errors=catch_definition.get("error_equals", ["States.ALL"]),
                    result_path=catch_definition.get("result_path", "$"),
                )

        # Create the actual state machine. Use environment role as the default role.
        state_machine_arn = job.get("state_machine_arn", self.pipeline_iam_role_arn)
        sfn = stepfunctions.StateMachine(
            self,
            f"{self.pipeline_name}",
            state_machine_name=f"{self.pipeline_name}",
            definition=definition,
            timeout=core.Duration.seconds(job.get("properties", {}).get("timeout", 3600)),
            role=iam.Role.from_role_arn(self, "DefaultPipelineRoleArn", state_machine_arn, mutable=False),
        )

        # Make the state machine reference available by putting its ARN to the parameter store.
        parameter_name = f"/dataall/{self.pipeline_name}/{self.stage}/step_function_arn"
        param = aws_ssm.StringParameter(
            self,
            f"stepfunction_arn_{self.pipeline_name}",
            parameter_name=parameter_name,
            string_value=sfn.state_machine_arn,
        )
        param.grant_read(iam.Role.from_role_arn(self, "dataall_state_machine_arn_param", self.pipeline_iam_role_arn))

        # Read the cron schedule configurations
        self.schedules = self.create_step_function_scheduler(pipeline.definition, sfn)

        # Sets the tags to the state function
        self.set_resource_tags(sfn)

        self.create_step_function_triggers(pipeline, sfn.state_machine_arn)

        self.state_machine = sfn
        self.state_machine_definition = definition

        return True

    def make_tag_str(self):
        """Gets stringified resource tags"""
        tag_array = [f"{{ 'Key': '{key}', 'Value': '{value}' }}" for key, value in self.resource_tags.items()]
        return ",".join(tag_array)
