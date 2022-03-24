from engine.sagemaker import endpoint_task
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
        self.pipeline_region = "eu-west-1"
        self.resource_tags = {}

    def set_resource_tags(self, resource):
        pass
    def make_tag_str(self):
        pass


def test_make_create_endpoint_task():
    stack = ATestStack()
    job = {
        "name": "prediction",
        "type": "sagemaker_endpoint",
        "endpoint": "$.irisep",
        "config": {"instance_type": "m5.xlarge"},
    }
    xs = endpoint_task.make_sagemaker_endpoint_task(stack, job, 0, 0)
    assert len(xs) == 2


def test_make_create_endpoint_task_hard_coded():
    stack = ATestStack()
    job = {
        "name": "prediction",
        "type": "sagemaker_endpoint",
        "config": {"instance_type": "m5.xlarge", "endpoint_config_name": "iris-ep"},
    }
    xs = endpoint_task.make_sagemaker_endpoint_task(stack, job, 0, 0)
    assert len(xs) == 2
