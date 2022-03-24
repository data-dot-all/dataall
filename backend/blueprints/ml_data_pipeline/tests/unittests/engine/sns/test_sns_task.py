import yaml
from engine.sns import sns_task
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
        self.accountid = "012345678912"

    def set_resource_tags(self, resource):
        """ Puts the tag to the resource """
        pass

def test_make_sns_task():
   stack = ATestStack()
   config = """
               name: sns_test_task
               description: "piblishing to an sns topic."
               type: sns_publish
               config:
                 topic_name: MySNSTopicName #created in the AWS resources
                 message: "ALL FILES LOADED"
            """
   job_config = yaml.safe_load(config)
   task = sns_task.make_publish_to_sns_task(stack, job_config)
   assert task




