from aws_cdk import core
from engine.sagemaker.mappers.sm_endpointconfig_mapper import SageMakerEndpointConfigPropsMapper
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


def test_map_props():
    stack = ATestStack()
    config = {"instance_type": "c5.2xlarge", "accelerator_type": "ml.eia1.medium", "timeout": 3600}
    props = SageMakerEndpointConfigPropsMapper.map_props(stack, "ep_name", config, "model_name")
    assert props["integration_pattern"]
    assert props["timeout"].to_seconds() == 3600
    assert len(props["production_variants"]) == 1

    pv = props["production_variants"][0]
    assert pv.accelerator_type.to_string() == "ml.eia1.medium"
    assert pv.initial_instance_count == 1
    assert pv.initial_variant_weight == 1
