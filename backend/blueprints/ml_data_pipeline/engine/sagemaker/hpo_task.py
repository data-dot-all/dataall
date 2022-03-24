import copy
import textwrap

from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda
from aws_cdk import aws_stepfunctions as stepfunctions
from aws_cdk import aws_stepfunctions_tasks as tasks
from aws_cdk.aws_lambda import Code

from engine.sagemaker.mappers.sm_hyperparameter_tuning_mapper import (
    SageMakerHyperparameterTuningPropsMapper,
)
from engine.sagemaker.model_task import make_sagemaker_model_task


def definition_from_config(stack, job, hpo_path, group_index, job_index):
    tokens = read_training_params_from_paths(job)
    tags = stepfunctions.TaskInput.from_data_at("$.job_names.tags").value

    definition = {
        "Type": "Task",
        "Resource": "arn:aws:states:::sagemaker:createHyperParameterTuningJob.sync",
        "ResultPath": hpo_path,
        "Parameters": SageMakerHyperparameterTuningPropsMapper.map_props(
            stack,
            job["config"],
            stepfunctions.TaskInput.from_data_at(
                f"$.job_names.{group_index}|{job_index}"
            ).value,
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


def make_sagemaker_hpo_task(stack, job, group_index, job_index):
    """Makes HPO task from configuration.

    Parameters
        stack target CDK Stack
        job   job configuration
        group_index the index of the job in a step function
        job_index inde of the job in a parallel

    """
    hpo_path = job.get("hpo_result_path", "$.hpo")

    get_best_model_fn = aws_lambda.Function(
        stack,
        "get_best_model_fn",
        code=Code.from_inline(
            textwrap.dedent(
                """
                def handler(event, context):
                    s3_base_path = event['TrainingJobDefinition']['OutputDataConfig']['S3OutputPath']
                    key_prefix = event['BestTrainingJob']['TrainingJobName'] + "/output/model.tar.gz"
                    
                    path = f"{s3_base_path}{key_prefix}" if s3_base_path[-1] == '/' else f"{s3_base_path}/{key_prefix}" 
                    return {
                        'statusCode': 200,
                        'path': path
                    }
                """
            )
        ),
        handler="index.handler",
        runtime=aws_lambda.Runtime.PYTHON_3_7,
        role=iam.Role.from_role_arn(
            stack, "GetBestModel", stack.pipeline_iam_role_arn, mutable=False
        ),
    )
    stack.set_resource_tags(get_best_model_fn)

    get_model_task = tasks.LambdaInvoke(
        stack,
        "Lambda: get_best_model",
        lambda_function=get_best_model_fn,
        result_path=job["config"].get("best_model_path", hpo_path + ".best_model"),
        input_path=hpo_path,
        payload_response_only=True,
    )

    # Read inputs that are defined in the step function input path
    definition = definition_from_config(stack, job, hpo_path, group_index, job_index)

    task = stepfunctions.CustomState(
        stack, "SageMaker HPO: " + job["name"], state_json=definition
    )

    chain = task.next(get_model_task)

    # Check if go ahead and create the model from the best model.
    if job.get("model"):
        model = copy.deepcopy(job.get("model"))
        model["name"] = "model-from-" + job.get("name", "")
        model["config"] = {
            "primary_container": {
                "algorithm": job["config"]["algorithm"],
                "model_path": job["config"].get(
                    "best_model_path", hpo_path + ".best_model"
                )
                + ".path",
            }
        }
        cmodel_task = make_sagemaker_model_task(stack, model, group_index, job_index)
        return chain.next(cmodel_task)
    else:
        return chain


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
