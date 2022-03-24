import re


class SageMakerProcessingJobPropsMappingException(Exception):
    def __init__(self, error, arg_name):
        super().__init__()
        self.message = (
            f"Failed to create SageMakerProcessingJobProps due to error: `{error}`"
        )

    def __str__(self):
        return self.message


class SageMakerProcessingJobPropsMapper:
    @classmethod
    def map_props(cls, stack, job_name, main_module, config_props, tags) -> dict:

        app_specification = SageMakerProcessingJobPropsMapper.map_app_specification(
            config_props, main_module, stack
        )

        environment = (
            f"{config_props.get('environment')}"
            if config_props.get("environment")
            else None
        )

        experiment_config = cls.map_experiment_config(config_props)

        network_config = cls.map_network_config(config_props)

        processing_inputs = cls.map_processing_inputs(config_props)

        processing_output_config = cls.map_processing_output_config(config_props)

        processing_resources = cls.map_processing_resources(config_props)

        stopping_condition = cls.map_stopping_condition(config_props)

        props = {
            "ProcessingJobName.$": job_name,
            "AppSpecification": app_specification,
            "Environment": environment,
            "ExperimentConfig": experiment_config,
            "NetworkConfig": network_config,
            "ProcessingInputs": processing_inputs,
            "ProcessingOutputConfig": processing_output_config,
            "ProcessingResources": processing_resources,
            "RoleArn": config_props.get("role", stack.pipeline_iam_role_arn),
            "StoppingCondition": stopping_condition,
            "Tags.$": tags,
        }
        if not props["ProcessingJobName.$"]:
            raise SageMakerProcessingJobPropsMappingException(
                Exception, "Job Name is Mandatory"
            )
        if not props["AppSpecification"]:
            raise SageMakerProcessingJobPropsMappingException(
                Exception, "AppSpecification is Mandatory"
            )
        if not props["ProcessingResources"]:
            raise SageMakerProcessingJobPropsMappingException(
                Exception, "ProcessingResources is Mandatory"
            )
        if not props["RoleArn"]:
            raise SageMakerProcessingJobPropsMappingException(
                Exception, "RoleArn is Mandatory"
            )

        props = cls.clean_dict_from_none_values(props)

        return props

    @classmethod
    def map_tags(cls, config_props):
        if config_props.get("tags"):
            tags = []
            for k, v in config_props.get("tags"):
                tags.append({"Key": k, "Value": v})
            return tags

    @classmethod
    def map_stopping_condition(cls, config_props):
        if config_props.get("stopping_condition"):
            stopping_condition = {
                "MaxRuntimeInSeconds": config_props["stopping_condition"]["max_runtime"]
            }
            return stopping_condition

    @classmethod
    def map_processing_resources(cls, config_props):
        processing_resources = {
            "ClusterConfig": dict(
                InstanceCount=1, InstanceType="ml.m4.xlarge", VolumeSizeInGB=35
            )
        }
        if config_props.get("processing_resources"):
            processing_resources = {
                "ClusterConfig": {
                    "InstanceCount": config_props["processing_resources"][
                        "cluster_config"
                    ]["instance_count"],
                    "InstanceType": config_props["processing_resources"][
                        "cluster_config"
                    ]["instance_type"],
                    "VolumeSizeInGB": config_props["processing_resources"][
                        "cluster_config"
                    ]["volume_size"],
                    "VolumeKmsKeyId": config_props["processing_resources"][
                        "cluster_config"
                    ].get("volume_encryption_key"),
                }
            }
        processing_resources = cls.clean_dict_from_none_values(processing_resources)
        return processing_resources

    @classmethod
    def map_processing_output_config(cls, config_props):
        if config_props.get("processing_output_config"):
            processing_output_config = dict()
            processing_output_config["KmsKeyId"] = config_props[
                "processing_output_config"
            ]["kms_key_id"]
            outputs = []
            for p in config_props.get("processing_output_config").get("outputs"):
                outputs.append(
                    {
                        "OutputName": p["output_name"],
                        "S3Output": {
                            "LocalPath": p["s3_output"]["local_path"],
                            "S3UploadMode": p["s3_output"]["s3_upload_mode"],
                            "S3Uri": p["s3_output"]["s3_uri"],
                        },
                    }
                )
            processing_output_config = cls.clean_dict_from_none_values(
                processing_output_config
            )
            return processing_output_config

    @classmethod
    def map_processing_inputs(cls, config_props):
        if config_props.get("processing_inputs"):
            processing_inputs = []
            for p in config_props.get("processing_inputs"):
                processing_inputs.append(
                    {
                        "InputName": p["input_name"],
                        "S3Input": {
                            "LocalPath": p["s3_input"]["local_path"],
                            "S3CompressionType": p["s3_input"]["compression_type"],
                            "S3DataDistributionType": p["s3_input"]["s3_data"][
                                "distribution_type"
                            ],
                            "S3DataType": p["s3_input"]["s3_data"]["type"],
                            "S3InputMode": p["s3_input"]["s3_input_mode"],
                            "S3Uri": p["s3_input"]["s3_uri"],
                        },
                    }
                )
            return processing_inputs

    @classmethod
    def map_network_config(cls, config_props):
        if config_props.get("network_config"):
            network_config = {
                "EnableInterContainerTrafficEncryption": config_props.get(
                    "network_config"
                ).get("enable_intercontainer_traffic_encryption"),
                "EnableNetworkIsolation": config_props.get("network_config").get(
                    "enable_network_isolation"
                ),
                "VpcConfig": {
                    "SecurityGroupIds": config_props.get("network_config").get(
                        "vpc_config"
                    )["security_groups"],
                    "Subnets": config_props.get("network_config").get("vpc_config")[
                        "subnets"
                    ],
                },
            }
            network_config = cls.clean_dict_from_none_values(network_config)
            return network_config

    @classmethod
    def map_experiment_config(cls, config_props):
        if config_props.get("experiment_config"):
            experiment_config = {
                "ExperimentName": f"{config_props['experiment_config'].get('experiment_name')}",
                "TrialComponentDisplayName": f"{config_props['experiment_config'].get('trial_component_display_name')}",
                "TrialName": f"{config_props['experiment_config'].get('trial_name')}",
            }
            experiment_config = cls.clean_dict_from_none_values(experiment_config)
            return experiment_config

    @classmethod
    def map_app_specification(cls, config_props, main_module, stack):
        container_image = stack.ecr_repository_uri
        container_entrypoint = ["python3", main_module]
        container_arguments = None
        if config_props.get("app_specification"):
            if config_props["app_specification"].get("container_image"):
                container_image = config_props["app_specification"]["container_image"]
            if config_props["app_specification"].get("container_entrypoint"):
                container_entrypoint = config_props["app_specification"][
                    "container_entrypoint"
                ]
            if config_props["app_specification"].get("container_arguments"):
                container_arguments = config_props["app_specification"][
                    "container_arguments"
                ]

        app_specification = {
            "ImageUri": container_image,
            "ContainerEntrypoint": container_entrypoint,
            "containerArguments": container_arguments,
        }
        return cls.clean_dict_from_none_values(app_specification)

    @classmethod
    def get_processing_job_name(cls, job_name):
        job_name = re.sub(r"[^a-zA-Z0-9-]", "", job_name).lower()
        return f"States.Format('{{}}-{job_name}', $$.Execution.Name)"

    @classmethod
    def clean_dict_from_none_values(cls, props):
        filtered = {k: v for k, v in props.items() if v is not None and v != "None"}
        props.clear()
        props.update(filtered)
        return props
