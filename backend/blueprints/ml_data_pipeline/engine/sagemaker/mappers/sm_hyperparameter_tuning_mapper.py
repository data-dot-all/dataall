import sagemaker
from engine.sagemaker.mappers.common_training_mapper import CommonTrainingMapper


class SageMakerHyperparameterTuningPropsMapper:
    @classmethod
    def map_props(cls, stack, config_props, job_name, tokens, tags) -> dict:
        """Converts the config defined in the configuration file into configuration of SageMaker HPO
        Parameters
            stack the enclosing stack
            config_props the properties as defined in the configuration file
            job_name the job name. Possibly taken from a step function path.
            tokens the list of values taken from step function paths.
        """
        return cls.map_hp_tuning_parameters(
            stack, config_props, job_name, tokens, stack.pipeline_iam_role_arn, tags
        )

    @classmethod
    def map_resource_limits(cls, res_config):
        """Configures the resource limits of an HPO job. It includes the number of training glue_jobs to be launched and how many
            parallel glue_jobs can be run at the same time.
        Parameters
            res_config the configuration
        """
        dict_result = {}

        dict_result["MaxNumberOfTrainingJobs"] = res_config.get("nb_of_training_jobs")
        dict_result["MaxParallelTrainingJobs"] = res_config.get(
            "max_parallel_training_jobs", 1
        )

        return dict_result

    @classmethod
    def map_objective(cls, node):
        return {"Type": node["type"], "MetricName": node["metric"]}

    @classmethod
    def map_parameter_ranges(cls, parameter_ranges):
        continuous_parameters = []
        integer_parameters = []
        categorical_parameters = []

        for parameter_range in parameter_ranges:
            if (
                parameter_range["type"] == "continuous"
                or parameter_range["type"] == "integer"
            ):

                parameter = {}
                parameter["Name"] = parameter_range["name"]
                parameter["MinValue"] = str(parameter_range["min_value"])
                parameter["MaxValue"] = str(parameter_range["max_value"])
                parameter["ScalingType"] = parameter_range.get("scaling_type", "Auto")

                if parameter_range["type"] == "continuous":
                    continuous_parameters.append(parameter)
                else:
                    integer_parameters.append(parameter)
            elif parameter_range["type"] == "category":
                categorical_parameters.append(parameter_range["values"])
            else:
                raise Exception(
                    "Unknown parameter type {}".format(parameter_range["type"])
                )

        result = {}
        if continuous_parameters:
            result["ContinuousParameterRanges"] = continuous_parameters
        if integer_parameters:
            result["IntegerParameterRanges"] = integer_parameters
        if categorical_parameters:
            result["CategoricalParameterRanges"] = categorical_parameters
        return result

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
    def map_static_hyperparameters(cls, static_params):
        return {param["name"]: str(param["value"]) for param in static_params}

    @classmethod
    def map_hp_tuning_parameters(cls, stack, config, job_name, tokens, roleARN, tags):
        result_dict = {}
        resource_dict = {
            resource["name"]: resource for resource in config.get("resources")
        }

        resource_limits = cls.map_resource_limits(config.get("resource_limits", {}))

        objective = cls.map_objective(config.get("objective", {}))

        algorithm_specification = cls.map_algorithm(stack, config["algorithm"])

        result_dict["HyperParameterTuningJobConfig"] = {
            "Strategy": "Bayesian",
            "HyperParameterTuningJobObjective": objective,
            "ResourceLimits": resource_limits,
            "ParameterRanges": cls.map_parameter_ranges(config["parameter_ranges"]),
        }

        if tokens.get("output_path_from_input"):
            s3OutputPath = {"S3OutputPath.$": tokens["output_path_from_input"]}
        else:
            bucket = config["output_data_path"]["bucket"]
            prefix_key = config["output_data_path"]["prefix_key"]
            s3URI = "s3://{}/{}".format(bucket, prefix_key)
            s3OutputPath = {"S3OutputPath": s3URI}

        result_dict["TrainingJobDefinition"] = {
            "AlgorithmSpecification": algorithm_specification,
            "OutputDataConfig": s3OutputPath,
            "StoppingCondition": {
                "MaxRuntimeInSeconds": config.get("max_runtime", "108000")
            },
            "ResourceConfig": cls.map_resources(config, resource_dict),
            "RoleArn": roleARN,
            "StaticHyperParameters": cls.map_static_hyperparameters(
                config.get("static_hyperparameters", {})
            ),
        }
        if config.get("training_input_from_path"):
            result_dict["TrainingJobDefinition"][
                "InputDataConfig"
            ] = cls.map_input_data_tokens(config, tokens)
        elif tokens.get("input_paths_from_input"):
            result_dict["TrainingJobDefinition"]["InputDataConfig.$"] = tokens[
                "input_paths_from_input"
            ]

        else:
            result_dict["TrainingJobDefinition"][
                "InputDataConfig"
            ] = cls.map_input_data_config(config)

        result_dict["HyperParameterTuningJobName.$"] = (
            tokens.get("ext_job_name") if tokens.get("ext_job_name") else job_name
        )
        result_dict["Tags.$"] = tags

        return result_dict
