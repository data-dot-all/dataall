class SageMakerBatchTransformJobPropsMappingException(Exception):
    def __init__(self, error, arg_name):
        super().__init__()
        self.message = f"Failed to create SageMakerBatchTransformJobProps due to error: `{error}` on {arg_name}"
        self.error = error
        self.arg_name = arg_name

    def __str__(self):
        return self.message


class SageMakerBatchTransformJobPropsMapper:
    @classmethod
    def map_data_processing(cls, config_props):
        dp = None
        if config_props.get("data_processing"):
            dp = {}
            dp_input = config_props.get("data_processing")
            if dp_input.get("input_filter"):
                dp["InputFilter"] = dp_input.get("input_filter")
            if dp_input.get("join_source"):
                dp["JoinSource"] = dp_input.get("join_source")
            if dp_input.get("output_filter"):
                dp["OutputFilter"] = dp_input.get("output_filter")
        return dp

    @classmethod
    def map_transform_input(cls, config_props):
        transform_input = config_props.get("transform_input")
        if not transform_input:
            raise SageMakerBatchTransformJobPropsMappingException(
                "Missing transform_input: transform_input {compression_type, content_type, s3_data_source}",
                "transform_input",
            )

        ti = {}
        if transform_input.get("compression_type"):
            ti["CompressionType"] = transform_input.get("compression_type").strip()

        if transform_input.get("content_type"):
            ti["ContentType"] = transform_input.get("content_type").strip()

        if transform_input.get("split_type"):
            ti["SplitType"] = transform_input.get("split_type")
        elif ti.get("ContentType") and ti.get("ContentType") == "text/csv":
            ti["SplitType"] = "Line"

        s3_data_source = transform_input.get("s3_data_source")
        s3_ds = {}
        s3_ds["S3DataType"] = s3_data_source.get("s3_data_type", "S3Prefix").strip()

        if (not s3_data_source.get("s3_uri_from_path")) and (
            not s3_data_source.get("s3_uri")
        ):
            raise SageMakerBatchTransformJobPropsMappingException(
                "Incomplete s3_data_source. Check s3_uri_from_path or s3_uri",
                "s3_data_source",
            )

        if s3_data_source.get("s3_uri_from_path"):
            s3_ds["S3Uri.$"] = s3_data_source.get("s3_uri_from_path").strip()
        else:
            s3_ds["S3Uri"] = s3_data_source.get("s3_uri").strip()

        ti["DataSource"] = {"S3DataSource": s3_ds}

        return ti

    @classmethod
    def map_transform_output(
        cls, config_props: dict, transform_input: dict, data_processing: dict
    ) -> dict:
        transform_output = config_props.get("transform_output")
        if not transform_output:
            raise SageMakerBatchTransformJobPropsMappingException(
                "Missing transform_output: transofrm_output {accept, kms_key_id, s3_output_path}",
                "transform_output",
            )

        tout = {}
        if transform_output.get("accept"):
            tout["Accept"] = transform_output.get("accept").strip()
        elif transform_input.get("ContentType") == "text/csv":
            tout["Accept"] = transform_input["ContentType"]

        if transform_output.get("kms_key_id"):
            tout["KmsKeyId"] = transform_output.get("kms_key_id").strip()

        if (not transform_output.get("s3_output_path_from_path")) and (
            not transform_output.get("s3_output_path")
        ):
            raise SageMakerBatchTransformJobPropsMappingException(
                "Incomplete s3_output_path. Check s3_output_path_from_path or s3_output_path",
                "s3_data_source",
            )

        if transform_output.get("s3_output_path_from_path"):
            tout["S3OutputPath.$"] = transform_output.get(
                "s3_output_path_from_path"
            ).strip()
        else:
            tout["S3OutputPath"] = transform_output.get("s3_output_path").strip()

        if transform_output.get("assemble_with"):
            tout["AssembleWith"] = transform_output.get("assemble_with")
        elif (
            data_processing
            and data_processing.get("JoinSource") == "Input"
            and transform_input.get("SplitType")
        ):
            tout["AssembleWith"] = transform_input.get("SplitType")
        return tout

    @classmethod
    def map_transform_resources(cls, config_props: dict) -> dict:
        transform_resources = config_props.get("transform_resources")
        tres = {}

        try:
            tres["InstanceCount"] = int(transform_resources.get("instance_count", "1"))
        except ValueError:
            raise SageMakerBatchTransformJobPropsMappingException(
                "Invalid instance_count at transform_resource. Expect integer",
                "instance_count",
            )

        if not transform_resources.get("instance_type"):
            raise SageMakerBatchTransformJobPropsMappingException(
                "Missing instance type for transform_resource", "instance_type"
            )

        tres["InstanceType"] = transform_resources.get("instance_type").strip()

        if tres.get("volume_kms_key_id"):
            tres["VolumeKmsKeyId"] = tres.get("volume_kms_key_id").strip()
        return tres

    @classmethod
    def map_props(cls, stack, config_props: dict, tags={}) -> dict:

        result = {}
        if config_props.get("batch_strategy"):
            result["BatchStrategy"] = config_props.get("batch_strategy")

        dp = cls.map_data_processing(config_props)
        if dp:
            result["DataProcessing"] = dp

        if config_props.get("max_concurrent_transforms"):
            try:
                dp["MaxConcurrentTransforms"] = int(
                    config_props.get("max_concurrent_transforms")
                )
            except ValueError:
                raise SageMakerBatchTransformJobPropsMappingException(
                    "Invalid value for max_concurrent_transforms {}".format(
                        config_props.get("max_concurrent_transforms")
                    ),
                    "max_concurrent_transforms",
                )

        result["Tags.$"] = tags

        if config_props.get("model_name"):
            result["ModelName"] = config_props.get("model_name")
        elif config_props.get("model_name_path"):
            result["ModelName.$"] = config_props.get("model_name_path")
        else:
            raise SageMakerBatchTransformJobPropsMappingException(
                "Need model name ", "model_name"
            )

        result["TransformInput"] = cls.map_transform_input(config_props)

        if config_props.get("transform_job_name_path"):
            result["TransformJobName.$"] = config_props.get("transform_job_name_path")
        elif config_props.get("transform_job_name"):
            result["TransformJobName"] = config_props.get("transfrom_job_name")

        result["TransformOutput"] = cls.map_transform_output(
            config_props, result["TransformInput"], result.get("DataProcessing")
        )
        result["TransformResources"] = cls.map_transform_resources(config_props)

        return result
