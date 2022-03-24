from aws_cdk import core
from engine.sagemaker.mappers.sm_model_mapper import SageMakerModelPropsMapper
from aws_cdk import aws_stepfunctions_tasks as stepfunctions_tasks


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
        self.pipeline_name = "pl"
        self.pipeline_region = "eu-west-1"
        self.stage = "test"
        self.resource_tags = {"tag1": "tag1_value"}
        self.tags_tracker = {}

    def set_resource_tags(self, resource):
        """ Puts the tag to the resource """
        pass


def test_map_props():
    stack = ATestStack()
    config = {
        "primary_container": {"algorithm": {"name": "forecasting-deepar"}, "model_path": "$.model_path"},
        "timeout": 1200,
    }
    props = SageMakerModelPropsMapper.map_props(stack, "forecasting", config)
    print(props)
    assert props["timeout"].to_seconds() == 1200
    assert isinstance(props["primary_container"], stepfunctions_tasks.ContainerDefinition)


def test_map_props_image_uri():
    stack = ATestStack()
    config = {
        "primary_container": {
            "algorithm" : {
                "image": "141502667606.dkr.ecr.eu-west-1.amazonaws.com/sagemaker-xgboost:1.2-1"
            },
            "model_path": "$.model_path",
        },
    }
    props = SageMakerModelPropsMapper.map_props(stack, "forecasting", config)
    print(props)
    assert props["timeout"].to_seconds() == 8200
    assert isinstance(props["primary_container"], stepfunctions_tasks.ContainerDefinition)


def test_map_props_hardcoded_model_input():
    stack = ATestStack()
    config = {
        "primary_container": {
            "algorithm" : {
                "image": "141502667606.dkr.ecr.eu-west-1.amazonaws.com/sagemaker-xgboost:1.2-1"
            },
            "model_path_from_bucket": {"bucket": "dhrareforecast", "prefix_key": "model.tar.gz"},
        },
    }
    props = SageMakerModelPropsMapper.map_props(stack, "forecasting", config)
    assert isinstance(props["primary_container"], stepfunctions_tasks.ContainerDefinition)
