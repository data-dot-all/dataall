import uuid

from aws_cdk import aws_ec2, aws_kms, aws_stepfunctions, core
from aws_cdk.aws_stepfunctions import TaskInput
from aws_cdk.aws_stepfunctions_tasks import AcceleratorType, ProductionVariant


class SageMakerEndpointConfigPropsMapper:
    @classmethod
    def map_props(
        cls, stack, endpoint_config_name, config_props: dict, model_name_from_input
    ) -> dict:
        endpoint_config = dict(
            heartbeat=config_props.get("heartbeat"),
            input_path=config_props.get("input_path"),
            integration_pattern=config_props.get("integration_pattern")
            or aws_stepfunctions.IntegrationPattern.REQUEST_RESPONSE,
            output_path=config_props.get("output_path"),
            result_path=config_props.get(
                "result_path", aws_stepfunctions.JsonPath.DISCARD
            ),
            timeout=core.Duration.seconds(config_props.get("timeout", 8200)),
            endpoint_config_name=endpoint_config_name,
            production_variants=cls.map_product_variants(
                config_props, model_name_from_input
            ),
            kms_key=aws_kms.Key.from_key_arn(
                stack,
                f"endpointkey-{str(uuid.uuid4())[:8]}",
                config_props.get("kms_key"),
            )
            if config_props.get("kms_key")
            else None,
        )
        return endpoint_config

    @classmethod
    def map_product_variants(
        cls, config_props, model_name_from_input
    ) -> [ProductionVariant]:
        production_variants = []
        instance_type = config_props["instance_type"]
        model_name = model_name_from_input or config_props["model_name"]
        production_variants.append(
            ProductionVariant(
                initial_instance_count=config_props.get("initial_instance_count", 1),
                instance_type=aws_ec2.InstanceType(
                    instance_type_identifier=instance_type
                ),
                model_name=model_name,
                variant_name=config_props.get("variant_name", f"{model_name}"),
                initial_variant_weight=1,
                accelerator_type=cls.map_accelerator_type(config_props),
            )
        )
        return production_variants

    @classmethod
    def map_accelerator_type(cls, pv):
        if pv.get("accelerator_type"):
            return AcceleratorType(instance_type_identifier=pv["accelerator_type"])
