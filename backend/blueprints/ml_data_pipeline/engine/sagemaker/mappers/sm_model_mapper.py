import uuid

import sagemaker
from aws_cdk import aws_ec2, aws_iam, aws_stepfunctions, core, aws_s3
from aws_cdk.aws_stepfunctions import TaskInput
from aws_cdk.aws_stepfunctions_tasks import (
    ContainerDefinition,
    DockerImage,
    Mode,
    S3Location,
)

from engine.sagemaker.prebuilt_extension_image_builder import (
    PrebuiltExtensionImageBuilder,
)


class SageMakerModelPropsMapper:
    @classmethod
    def map_props(cls, stack, model_name, config_props: dict) -> dict:
        model = dict(
            heartbeat=config_props.get("heartbeat"),
            input_path=config_props.get("input_path"),
            integration_pattern=config_props.get("integration_pattern")
            or aws_stepfunctions.IntegrationPattern.REQUEST_RESPONSE,
            output_path=config_props.get("output_path"),
            result_path=config_props.get(
                "result_path", aws_stepfunctions.JsonPath.DISCARD
            ),
            timeout=core.Duration.seconds(config_props.get("timeout", 8200)),
            model_name=model_name,
            primary_container=cls.map_primary_container(stack, config_props),
            enable_network_isolation=config_props.get("enable_network_isolation")
            or False,
            role=cls.map_role(stack, config_props),
        )
        return model

    @classmethod
    def map_primary_container(cls, stack, config_props):
        print("map_primary_container", config_props)
        if config_props["primary_container"]["algorithm"].get("name"):
            container_uri = sagemaker.image_uris.retrieve(
                framework=config_props["primary_container"]["algorithm"]["name"],
                region=stack.pipeline_region,
                version=config_props["primary_container"]["algorithm"].get(
                    "version", "latest"
                ),
            )
        elif config_props["primary_container"]["algorithm"].get("pre_built"):
            container_uri = PrebuiltExtensionImageBuilder.image_uri_from_main_module(
                config_props["primary_container"]["algorithm"]["pre_built"]["module"]
            )

        else:
            container_uri = config_props["primary_container"]["algorithm"]["image"]

        if config_props["primary_container"].get("model_path"):
            s3_location = S3Location.from_json_expression(
                config_props["primary_container"]["model_path"]
            )
        else:
            bucket = aws_s3.Bucket.from_bucket_name(
                stack,
                id=f"primarybucket-{str(uuid.uuid4())[:8]}",
                bucket_name=config_props["primary_container"]["model_path_from_bucket"][
                    "bucket"
                ],
            )

            s3_location = S3Location.from_bucket(
                bucket,
                config_props["primary_container"]["model_path_from_bucket"][
                    "prefix_key"
                ],
            )

        primary_container = ContainerDefinition(
            image=DockerImage.from_registry(container_uri),
            mode=Mode.SINGLE_MODEL,
            model_s3_location=s3_location,
        )

        return primary_container

    @classmethod
    def map_role(cls, stack, config_props):
        return aws_iam.Role.from_role_arn(
            stack,
            f"sgmTrainingRole-{str(uuid.uuid4())[:8]}",
            config_props.get("role", stack.pipeline_iam_role_arn),
            mutable=False,
        )
