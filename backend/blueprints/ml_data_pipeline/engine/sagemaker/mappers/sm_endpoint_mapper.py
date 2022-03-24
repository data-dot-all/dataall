from aws_cdk import aws_stepfunctions, core
from aws_cdk.aws_stepfunctions import TaskInput


class SageMakerEndpointPropsMapper:
    @classmethod
    def map_props(cls, endpoint_name, endpoint_config_name, config_props: dict) -> dict:
        endpoint = dict(
            heartbeat=config_props.get("heartbeat"),
            input_path=config_props.get("input_path"),
            integration_pattern=config_props.get("integration_pattern")
            or aws_stepfunctions.IntegrationPattern.REQUEST_RESPONSE,
            output_path=config_props.get("output_path"),
            result_path=config_props.get("result_path")
            or aws_stepfunctions.JsonPath.DISCARD,
            timeout=core.Duration.seconds(config_props.get("timeout", 8200)),
            endpoint_name=endpoint_name,
            endpoint_config_name=endpoint_config_name,
            comment=config_props.get("description"),
        )
        return endpoint
