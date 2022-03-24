import sagemaker
from engine.sagemaker.prebuilt_extension_image_builder import (
    PrebuiltExtensionImageBuilder,
)


class CommonTrainingMapper:
    @classmethod
    def map_algorithm(cls, stack, config):
        if config.get("name"):
            container_uri = sagemaker.image_uris.retrieve(
                framework=config["name"],
                region=stack.pipeline_region,
                version=config.get("version", "latest"),
            )
            print("container_uri of AWS algorithm {}".format(container_uri))

        elif config.get("pre_built"):
            container_uri = PrebuiltExtensionImageBuilder.image_uri_from_main_module(
                config["pre_built"]["module"]
            )

            print("container_uri of pre_built: {}".format(container_uri))

        else:
            container_uri = config["training_image"]
            print("container_uri from parameter {}".format(container_uri))

        algorithm_specification = {}
        algorithm_specification["TrainingImage"] = container_uri
        algorithm_specification["TrainingInputMode"] = config.get(
            "training_input_mode", "File"
        )

        if config.get("metric_definitions"):
            algorithm_specification["MetricDefinitions"] = [
                {"Name": m["name"], "Regex": m["regex"]}
                for m in config["metric_definitions"]
            ]

        return algorithm_specification

    @classmethod
    def map_resources(cls, config, resource_dict):
        resource = resource_dict[config.get("resource_ref")]
        result = {}
        result["InstanceCount"] = resource.get("instance_count", "1")
        result["InstanceType"] = resource.get("instance_type", "ml.m5.2xlarge")
        if resource.get("volume_size"):
            result["VolumeSizeInGB"] = resource.get("volume_size")

        return result

    @classmethod
    def map_input_data_tokens(cls, config, tokens):

        training_input_from_path = tokens["training_input_from_path"]

        training_data_source = {}

        training_data_source["ChannelName"] = "train"
        if training_input_from_path.get("content_type"):
            training_data_source["ContentType.$"] = training_input_from_path[
                "content_type"
            ]
        else:
            training_data_source["ContentType"] = "text/csv"

        train_bucket_path = training_input_from_path["train_s3_uri"]["bucket"]
        train_prefix_key_path = training_input_from_path["train_s3_uri"]["prefix_key"]
        train_s3UriPath = f"States.Format('s3://{{}}/{{}}',{train_bucket_path}, {train_prefix_key_path})"
        training_data_source["DataSource"] = {
            "S3DataSource": {
                "S3DataDistributionType": "FullyReplicated",
                "S3DataType": "S3Prefix",
                "S3Uri.$": train_s3UriPath,
            }
        }
        input_data_config = [training_data_source]

        if training_input_from_path.get("validation_s3_uri"):
            validation_bucket_path = training_input_from_path["validation_s3_uri"][
                "bucket"
            ]
            validation_prefix_key_path = training_input_from_path["validation_s3_uri"][
                "prefix_key"
            ]
            validation_s3UriPath = f"States.Format('s3://{{}}/{{}}',{validation_bucket_path}, {validation_prefix_key_path})"

            validation_data_source = {}
            validation_data_source["ChannelName"] = "validation"
            if training_input_from_path.get("content_type"):
                validation_data_source["ContentType.$"] = training_input_from_path[
                    "content_type"
                ]
            else:
                validation_data_source["ContentType"] = "text/csv"

            validation_data_source["DataSource"] = {
                "S3DataSource": {
                    "S3DataDistributionType": "FullyReplicated",
                    "S3DataType": "S3Prefix",
                    "S3Uri.$": validation_s3UriPath,
                }
            }
            input_data_config.append(validation_data_source)

        if training_input_from_path.get("test_s3_uri"):
            test_data_source = {}
            test_bucket_path = training_input_from_path["test_s3_uri"]["bucket"]
            test_prefix_key_path = training_input_from_path["test_s3_uri"]["prefix_key"]
            test_s3UriPath = f"States.Format('s3://{{}}/{{}}',{test_bucket_path}, {test_prefix_key_path})"
            test_data_source["ChannelName"] = "test"
            if training_input_from_path.get("content_type"):
                test_data_source["ContentType.$"] = training_input_from_path[
                    "content_type"
                ]
            else:
                test_data_source["ContentType"] = "text/csv"
            test_data_source["DataSource"] = {
                "S3DataSource": {
                    "S3DataDistributionType": "FullyReplicated",
                    "S3DataType": "S3Prefix",
                    "S3Uri.$": test_s3UriPath,
                }
            }
            input_data_config.append(test_data_source)
        return input_data_config

    @classmethod
    def map_input_data_config(cls, config):

        input_data = config["input_data"]
        bucket = input_data["bucket"]
        content_type = input_data.get("content_type", "text/csv")

        training_data = input_data["training_data"]
        prefix = training_data["prefix_key"]
        s3URI = "s3://{}/{}".format(bucket, prefix)
        training_data_source = {}

        training_data_source["ChannelName"] = "train"
        training_data_source["ContentType"] = content_type
        training_data_source["DataSource"] = {
            "S3DataSource": {
                "S3DataDistributionType": "FullyReplicated",
                "S3DataType": "S3Prefix",
                "S3Uri": s3URI,
            }
        }

        input_data_config = [training_data_source]

        validation_data = input_data.get("validation_data")
        if validation_data:
            validation_data_source = {}
            validation_data_source["ChannelName"] = "validation"
            prefix = validation_data["prefix_key"]
            s3URI = "s3://{}/{}".format(bucket, prefix)
            validation_data_source["ContentType"] = content_type
            validation_data_source["DataSource"] = {
                "S3DataSource": {
                    "S3DataDistributionType": "FullyReplicated",
                    "S3DataType": "S3Prefix",
                    "S3Uri": s3URI,
                }
            }
            input_data_config.append(validation_data_source)

        test_data = input_data.get("test_data")
        if test_data:
            test_data_source = {}
            test_data_source["ChannelName"] = "test"
            prefix = test_data["prefix_key"]
            s3URI = "s3://{}/{}".format(bucket, prefix)
            test_data_source["ContentType"] = content_type
            test_data_source["DataSource"] = {
                "S3DataSource": {
                    "S3DataDistributionType": "FullyReplicated",
                    "S3DataType": "S3Prefix",
                    "S3Uri": s3URI,
                }
            }
            input_data_config.append(test_data_source)

        return input_data_config
