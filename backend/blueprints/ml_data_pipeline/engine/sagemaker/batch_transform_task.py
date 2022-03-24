from engine.sagemaker.mappers.sm_batch_transform_mapper import (
    SageMakerBatchTransformJobPropsMapper,
)
from aws_cdk import aws_stepfunctions as stepfunctions


def make_sagemaker_batch_transform_task(stack, job):
    """Makes batch transform job
    Before creating the transform job, it checks if the  transform job exists. If it exists, then
    it first deletes the job, and only then it creates/
    """
    definition = {
        "Type": "Task",
        "Resource": "arn:aws:states:::sagemaker:createTransformJob.sync",
        "ResultPath": "$.batch_transformation_output",
        "Parameters": SageMakerBatchTransformJobPropsMapper.map_props(
            stack,
            job["config"],
            stepfunctions.TaskInput.from_data_at("$.job_names.tags").value,
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
        stack, f'SageMaker Batch: {job["name"]}', state_json=definition
    )
