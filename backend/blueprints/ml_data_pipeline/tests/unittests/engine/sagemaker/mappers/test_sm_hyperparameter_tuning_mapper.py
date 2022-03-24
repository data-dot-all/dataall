from aws_cdk import core
from engine.sagemaker.mappers.sm_hyperparameter_tuning_mapper import SageMakerHyperparameterTuningPropsMapper
from aws_cdk import aws_stepfunctions as stepfunctions


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


def test_map_input_data_tokens():

    token_content = {}
    token_content["content_type"] = stepfunctions.TaskInput.from_data_at("$.content_type").value
    token_content["train_s3_uri"] = {
        "bucket": stepfunctions.TaskInput.from_data_at("$.train_bucket").value,
        "prefix_key": stepfunctions.TaskInput.from_data_at("$.train_prefix_key").value,
    }
    token_content["validation_s3_uri"] = {
        "bucket": stepfunctions.TaskInput.from_data_at("$.validation_bucket").value,
        "prefix_key": stepfunctions.TaskInput.from_data_at("$.validation_prefix_key").value,
    }
    props = SageMakerHyperparameterTuningPropsMapper.map_input_data_tokens(
        config={}, tokens={"training_input_from_path": token_content}
    )

    assert len(props) == 2

    train = props[0]
    validation = props[1]

    assert train["ContentType.$"]
    assert train["DataSource"]["S3DataSource"]["S3Uri.$"]
    assert validation["ContentType.$"]
    assert validation["DataSource"]["S3DataSource"]["S3Uri.$"]


def test_map_input_data_tokens_default_content_type():
    token_content = {}
    token_content["train_s3_uri"] = {
        "bucket": stepfunctions.TaskInput.from_data_at("$.train_bucket").value,
        "prefix_key": stepfunctions.TaskInput.from_data_at("$.train_prefix_key").value,
    }
    token_content["validation_s3_uri"] = {
        "bucket": stepfunctions.TaskInput.from_data_at("$.validation_bucket").value,
        "prefix_key": stepfunctions.TaskInput.from_data_at("$.validation_prefix_key").value,
    }
    token_content["test_s3_uri"] = {
        "bucket": stepfunctions.TaskInput.from_data_at("$.test_bucket").value,
        "prefix_key": stepfunctions.TaskInput.from_data_at("$.test_prefix_key").value,
    }
    props = SageMakerHyperparameterTuningPropsMapper.map_input_data_tokens(
        config={}, tokens={"training_input_from_path": token_content}
    )
    assert props[0]["ContentType"] == "text/csv"
    assert props[1]["ContentType"] == "text/csv"
    assert props[2]["ContentType"] == "text/csv"
