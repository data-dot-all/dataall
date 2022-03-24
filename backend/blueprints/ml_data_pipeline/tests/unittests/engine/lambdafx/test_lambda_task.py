import yaml
from engine.lambdafx import lambda_task
from aws_cdk import core

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
        self.pipeline_name = "very-long-pipeline-name"
        self.pipeline_region = "eu-west-1"
        self.stage = "test"
        self.resource_tags = {"tag1": "tag1_value"}
        self.tags_tracker = {}

    def set_resource_tags(self, resource):
        """ Puts the tag to the resource """
        pass

def test_function_name():
    stack = ATestStack()
    config = """
               name: prepare function very long so it throws exception
               description: "Preparing training and test data for iris dataset."
               type: lambda_function
               config:
                  entry: "tests/customcode/lambda_functions/prepare_iris"
                  timeout: 300
                  memory_size : 2056
            """
    
    name_too_long = False
    try:
        job_config = yaml.safe_load(config)
        lambda_task.get_function_name(stack, job_config)
    except:
        name_too_long = True
    assert name_too_long

    config_2 = """
               name: prepare function
               description: "Preparing training and test data for iris dataset."
               type: lambda_function
               config:
                  entry: "tests/customcode/lambda_functions/prepare_iris"
                  timeout: 300
                  memory_size : 2056
            """
    job_config_2 = yaml.safe_load(config_2)

    assert lambda_task.get_function_name(stack, job_config_2) == "very-long-pipeline-name-prepare function"

    stack.pipeline_name = "very-very-very-very-long-pipelne-namedslkfjqsdlkjfklsdjfkqsjdfkjqsdkfjsqdkmlfj"
    assert lambda_task.get_function_name(stack, job_config_2) == "very-very-very-very--mlfj-prepare function"

def test_make_lambdafx_task():

   stack = ATestStack()
   config = """
               name: prepare_function
               description: "Preparing training and test data for iris dataset."
               type: lambda_function
               config:
                  entry: "tests/customcode/lambda_functions/prepare_iris"
                  timeout: 300
                  memory_size : 2056
            """
   job_config = yaml.safe_load(config)
   task = lambda_task.make_lambda_function_task(stack, job_config)
   assert task




