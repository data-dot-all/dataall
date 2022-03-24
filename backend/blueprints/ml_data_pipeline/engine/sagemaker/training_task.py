import copy
from aws_cdk import aws_stepfunctions as stepfunctions


from engine.sagemaker.mappers.sm_training_mapper import SageMakerTrainingJobPropsMapper
from engine.sagemaker.model_task import make_sagemaker_model_task


def definition_from_config(stack, job, training_path, group_index, job_index):
    """Creates the definition of the step function task related to training job
    from the configuration.

    Parameters
        stack: the stack
        job: the job configuration
        training_path: the path where the training artefact is stored
        group_index: the group index of the task in the step function
        job_index: the job index of the task inside a group

    """
    tokens = read_training_params_from_paths(job)
    tags = stepfunctions.TaskInput.from_data_at("$.job_names.tags").value
    definition = {
        "Type": "Task",
        "Resource": "arn:aws:states:::sagemaker:createTrainingJob.sync",
        "ResultPath": training_path,
        "Parameters": SageMakerTrainingJobPropsMapper.map_props(
            stack,
            stepfunctions.TaskInput.from_data_at(
                f"$.job_names.{group_index}|{job_index}"
            ).value,
            job.get("main", {}),
            job["config"],
            tokens,
            tags=tags,
        ),
    }

    # Define retry only for SageMakerException.
    retry_definition = job.get("retry")
    if retry_definition:
        definition["Retry"] = [
            {
                "ErrorEquals": ["SageMaker.AmazonSageMakerException"],
                "IntervalSeconds": retry_definition.get("interval_seconds", 1),
                "MaxAttempts": retry_definition.get("retry_attempt", 3),
                "BackoffRate": retry_definition.get("backoff_rate", 1.1),
            }
        ]

    return definition


def read_training_params_from_paths(job):
    """Reads input paths from job configuration. Currently supported are:
    1. input_paths_from_input retrieve S3 input paths of the training glue_jobs from the input of the task.
    2. output_path_from_input retreieve S3 output paths of the training glue_jobs from the output of the task.
    3. ext_job_name the hpo job name.

    Parameter
        job: configuration
    """
    cfg = job.get("config")
    tokens = {}
    if cfg.get("input_paths_from_input"):
        tokens["input_paths_from_input"] = stepfunctions.TaskInput.from_data_at(
            cfg["input_paths_from_input"]
        ).value
    elif cfg.get("training_input_from_path"):
        training_input_dict = {}
        tokens["training_input_from_path"] = training_input_dict
        tifp = cfg.get("training_input_from_path")

        training_input_dict["content_type"] = stepfunctions.TaskInput.from_data_at(
            tifp["content_type"]
        ).value

        training_input_dict["train_s3_uri"] = {
            "bucket": stepfunctions.TaskInput.from_data_at(
                tifp["train_s3_uri"]["bucket"]
            ).value,
            "prefix_key": stepfunctions.TaskInput.from_data_at(
                tifp["train_s3_uri"]["prefix_key"]
            ).value,
        }

        if tifp.get("validation_s3_uri"):
            training_input_dict["validation_s3_uri"] = {
                "bucket": stepfunctions.TaskInput.from_data_at(
                    tifp["validation_s3_uri"]["bucket"]
                ).value,
                "prefix_key": stepfunctions.TaskInput.from_data_at(
                    tifp["validation_s3_uri"]["prefix_key"]
                ).value,
            }

        if tifp.get("test_s3_uri"):
            training_input_dict["test_s3_uri"] = {
                "bucket": stepfunctions.TaskInput.from_data_at(
                    tifp["test_s3_uri"]["bucket"]
                ).value,
                "prefix_key": stepfunctions.TaskInput.from_data_at(
                    tifp["test_s3_uri"]["prefix_key"]
                ).value,
            }
    if cfg.get("output_path_from_input"):
        tokens["output_path_from_input"] = stepfunctions.TaskInput.from_data_at(
            cfg["output_path_from_input"]
        ).value

    if job.get("ext_job_name"):
        tokens["ext_job_name"] = stepfunctions.TaskInput.from_data_at(
            job["ext_job_name"]
        ).value

    return tokens


def make_sagemaker_training_task(stack, job, group_index, job_index):
    """Makes Training task from configuration.

    Parameters
        stack target CDK Stack
        job   job configuration
        group_index the index of the job in a step function
        job_index inde of the job in a parallel

    """
    training_path = job.get("training_result_path", "$.training")

    definition = definition_from_config(
        stack, job, training_path, group_index, job_index
    )
    print(definition)
    task = stepfunctions.CustomState(
        stack, "Task " + job["name"], state_json=definition
    )

    # Whether or not to go on and create model.
    if job.get("model"):
        model = copy.deepcopy(job.get("model"))
        model["name"] = "model-from-" + job.get("name", "")

        if job["config"]["algorithm"].get("training_image"):
            model["config"] = {
                "primary_container": {
                    "algorithm": {
                        "image": job["config"]["algorithm"]["training_image"],
                    },
                    "model_path": "$.training.ModelArtifacts.S3ModelArtifacts",
                }
            }
        else:
            model["config"] = {
                "primary_container": {
                    "algorithm": job["config"]["algorithm"],
                    "model_path": "$.training.ModelArtifacts.S3ModelArtifacts",
                }
            }

        cmodel_task = make_sagemaker_model_task(stack, model, group_index, job_index)
        return task.next(cmodel_task)
    else:
        return task
