import sagemaker
from engine.sagemaker.mappers.common_training_mapper import CommonTrainingMapper
import copy


class SageMakerTrainingJobPropsMapper:
    @classmethod
    def map_props(cls, stack, job_name, main_entry, config_props, tokens, tags) -> dict:
        return cls.map_training_parameters(
            stack, config_props, job_name, tokens, tags, stack.pipeline_iam_role_arn
        )

    @classmethod
    def map_algorithm(cls, stack, config):
        return CommonTrainingMapper.map_algorithm(stack, config)

    @classmethod
    def map_resources(cls, config, resource_dict):
        return CommonTrainingMapper.map_resources(config, resource_dict)

    @classmethod
    def map_input_data_tokens(cls, config, tokens):
        return CommonTrainingMapper.map_input_data_tokens(config, tokens)

    @classmethod
    def map_input_data_config(cls, config):
        return CommonTrainingMapper.map_input_data_config(config)

    @classmethod
    def map_hyperparameters(cls, config_props):
        return config_props.get("hyperparameters")

    @classmethod
    def map_experiment_config(cls, config_props):
        experiment = config_props.get("experiment")
        return {
            "ExperimentName.$": experiment.get("experiment_name"),
            "TrialComponentDisplayName.$": experiment.get("trial"),
        }

    @classmethod
    def map_training_parameters(cls, stack, config, job_name, tokens, tags, roleARN):
        result_dict = {}
        resource_dict = {
            resource["name"]: resource for resource in config.get("resources")
        }

        algorithm_specification = cls.map_algorithm(stack, config["algorithm"])

        if tokens.get("output_path_from_input"):
            s3OutputPath = {"S3OutputPath.$": tokens["output_path_from_input"]}
        else:
            bucket = config["output_data_path"]["bucket"]
            key_prefix = config["output_data_path"]["key_prefix"]
            s3URI = "s3://{}/{}".format(bucket, key_prefix)
            s3OutputPath = {"S3OutputPath": s3URI}

        result_dict = {
            "AlgorithmSpecification": algorithm_specification,
            "OutputDataConfig": s3OutputPath,
            "StoppingCondition": {
                "MaxRuntimeInSeconds": config.get("max_runtime")
                or config.get("timeout", 108000)
            },
            "ResourceConfig": cls.map_resources(config, resource_dict),
            "RoleArn": roleARN,
        }
        if config.get("hyperparameters"):
            result_dict["HyperParameters"] = cls.map_hyperparameters(config)
        elif config.get("hyperparameters_from_path"):
            result_dict["HyperParameters.$"] = config.get("hyperparameters_from_path")

        if config.get("training_input_from_path"):
            result_dict["InputDataConfig"] = cls.map_input_data_tokens(config, tokens)
        elif tokens.get("input_paths_from_input"):
            result_dict["InputDataConfig.$"] = tokens["input_paths_from_input"]

        else:
            result_dict["InputDataConfig"] = cls.map_input_data_config(config)

        if config.get("experiment"):
            result_dict["ExperimentConfig"] = cls.map_experiment_config(config)

        result_dict["TrainingJobName.$"] = (
            tokens.get("ext_job_name") if tokens.get("ext_job_name") else job_name
        )

        result_dict["Tags.$"] = tags

        return result_dict
