from aws_cdk import core
from utils import stack_util
import yaml

class ATestStack(core.Stack):
    def __init__(self, **kwargs):
        super().__init__(None, **kwargs)
        self.env = {
            "CDK_DEFAULT_ACCOUNT": "012345678912",
            "CDK_DEFAULT_REGION": "eu-west-1",
        }
        self.pipeline_iam_role_arn = "arn:aws:iam::012345678901:role/dhdatasciencedevoqtnpj"
        self.pipeline_fulldev_iam_role = "arn:aws:iam::012345678901:role/dhdatasciencedevoqtnpj"
        self.pipeline_admin_iam_role = "arn:aws:iam::012345678901:role/dhdatasciencedevoqtnpj"
        self.ecr_repository_uri = "dkr.012345678912.eu-west-1"
        self.layer_versions = {}
        self.pipeline_name = "pl"
        self.pipeline_region = "eu-west-1"
        self.stage = "test"
        self.resource_tags = {"tag1": "tag1_value"}
        self.tags_tracker = {}

    def set_resource_tags(self, resource):
        """ Puts the tag to the resource """
        pass


def test_template_from_string():
    """ Tests template from configuration given in a string, instead of file."""
    config = """
name : Irispipeline
comment: Iris pipeline from preparation to deployment
aws_resources:

  - name: datascience_layer
    type: lambda_layer
    config:
       layer_entry: "customcode/lambda_layers/pandas_sklearn"
       bundle_type: custom
       cmd: "rm -rf /asset-output/python  && pip install -r requirements.txt --target /asset-output/python --quiet &&  rm -rf /asset-output/python/scipy* && rm -rf /asset-output/python/numpy*"

  - name: numpy_scipy37
    type: lambda_layer
    config:
        layer_arn:
                arn: "arn:aws:lambdafx:eu-west-1:399891621064:layer:AWSLambda-Python37-SciPy1x:37"
                id: "scipynumpy"
triggers:
  - name: "Trigger"
    type: glue
    config: job1.yaml
groups:

  - name: "Prepare_iris_data"
    glue_jobs:
      - name: prepare_function
        description: "Preparing training and test data for iris dataset at the bucket."
        type: lambda_function
        config:
          entry: "tests/customcode/lambda_functions/prepare_iris"
          layer_ref:
             - datascience_layer
             - numpy_scipy37
          timeout: 300
"""
    stack = ATestStack()
    failed_for_glue = False
    try: 
       pipeline = yaml.safe_load(config)
       stack_util.create_step_function_triggers(stack, pipeline, "arn:aws:states:eu-west-1:0123456789012:stateMachine:short-term-pipeline")
    except:
        failed_for_glue = True
    assert failed_for_glue
