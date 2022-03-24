from aws_cdk import aws_stepfunctions as stepfunctions

from engine.sagemaker.mappers.sm_processing_mapper import (
    SageMakerProcessingJobPropsMapper,
)


def make_sagemaker_processing_task(stack, job, group_index, job_index):
    tags = stepfunctions.TaskInput.from_data_at("$.job_names.tags").value
    definition = {
        "Type": "Task",
        "Resource": "arn:aws:states:::sagemaker:createProcessingJob.sync",
        "ResultPath": None,
        "Parameters": SageMakerProcessingJobPropsMapper.map_props(
            stack,
            stepfunctions.TaskInput.from_data_at(
                f"$.job_names.{group_index}|{job_index}"
            ).value,
            job["main"],
            job["config"],
            tags=tags,
        ),
    }
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
    return stepfunctions.CustomState(
        stack, "SageMaker Processing: " + job["name"], state_json=definition
    )
