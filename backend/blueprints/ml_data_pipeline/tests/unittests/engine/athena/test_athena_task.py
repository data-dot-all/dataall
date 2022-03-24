import yaml
from engine.athena import athena_task
from aws_cdk import core

class ATestStack(core.Stack):
    def __init__(self, **kwargs):
        super().__init__(None, **kwargs)
        self.env = {
            "CDK_DEFAULT_ACCOUNT": "012345678912",
            "CDK_DEFAULT_REGION": "eu-west-1",
        }
        self.pipeline_iam_role_arn = "arn:aws:iam::012345678901:role/dhdatasciencedevoqtnpj"
        self.ecr_repository_uri = "dkr.012345678912.eu-west-1"
        self.layer_versions = {}
        self.pipeline_name = "very-long-pipeline-name"
        self.pipeline_region = "eu-west-1"
        self.stage = "test"
        self.resource_tags = {"tag1": "tag1_value"}
        self.tags_tracker = {}

    def set_resource_tags(self, resource):
        """ Puts the tag to the resource """
        pass

def test_make_athena_task():
   stack = ATestStack()

   config = """              
       name: MyAthenaFunction
       type: athena_query
       comment: "describe me please"
       config:
           config_file: "customcode/athena/athena_jobs/example.yaml"  # it configures the athena job
           workgroup: primary  # we can reference the previously created workgroup
           # If no workgroup is assigned, then the environment-ADgroup workgroup is chosen by default
           retry:  # Optional, if no retry parameters are assigned, no retry strategy is configured
               error_equals: ["Athena.AmazonAthenaException", "Athena.TooManyRequestsException"]
               interval_seconds: 1
               retry_attempts: 5
               backoff_rate: 2
           variables:  # we can pass variables and referenced variables
               dimension: classification
               model_name: example
            """
   job_config = yaml.safe_load(config)
   task = athena_task.make_athena_query_task(stack, job_config)
   assert task




