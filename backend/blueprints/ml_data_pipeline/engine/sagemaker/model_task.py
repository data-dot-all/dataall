import textwrap
import re
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda
from aws_cdk import aws_stepfunctions as stepfunctions
from aws_cdk import aws_stepfunctions_tasks as tasks
from aws_cdk.aws_lambda import Code
from engine.sagemaker.mappers.sm_model_mapper import SageMakerModelPropsMapper


def make_sagemaker_model_task(stack, job, group_index, job_index):
    index = f"{group_index}|{job_index}"
    model_name = re.sub(r"[^a-zA-Z0-9-]", "", job["name"]).lower()
    delete_model = aws_lambda.Function(
        stack,
        f"deleteModel-{model_name}-{index}",
        code=Code.from_inline(
            textwrap.dedent(
                """
                import boto3
                from botocore.exceptions import ClientError
                import logging
                logger = logging.getLogger()
                logger.setLevel(logging.INFO)

                sagemaker = boto3.client('sagemaker')
                def handler(event, context):
                    logger.info(f"Received Event {event}")
                    try:
                        response = sagemaker.describe_model(
                          ModelName=event["model_name"]
                        )
                        model_exists = True
                        if response and response.get("ModelName"):
                            response = sagemaker.delete_model(
                              ModelName=event["model_name"]
                            )
                            model_exists = False
                    except ClientError as e:
                        logger.info("Error Deleting Model")
                        model_exists = True
                    return model_exists
                """
            )
        ),
        handler="index.handler",
        role=iam.Role.from_role_arn(
            stack,
            f"verifymodelrole{index}-{model_name}",
            stack.pipeline_iam_role_arn,
            mutable=False,
        ),
        runtime=aws_lambda.Runtime.PYTHON_3_7,
    )
    stack.set_resource_tags(delete_model)

    if job.get("model_name_path"):
        delete_payload = stepfunctions.TaskInput.from_object(
            {"model_name.$": job["model_name_path"]}
        )
    else:
        delete_payload = stepfunctions.TaskInput.from_object(
            {"model_name": re.sub(r"[^a-zA-Z0-9-]", "", job["name"]).lower()}
        )
    delete_model_task = tasks.LambdaInvoke(
        stack,
        f"Lambda: Delete Model {job['name']} If exists",
        lambda_function=delete_model,
        payload=delete_payload,
        payload_response_only=True,
        result_path="$.model",
    )
    if job.get("model_name_path"):
        mname = stepfunctions.TaskInput.from_data_at(job["model_name_path"]).value
    else:
        mname = model_name

    task_create_model = tasks.SageMakerCreateModel(
        stack,
        "SageMaker: Create Model " + job["name"],
        **SageMakerModelPropsMapper.map_props(stack, mname, job["config"]),
    )

    # Define retry only for SageMakerException.
    retry_definition = job.get("retry", {})
    task_create_model.add_retry(
        backoff_rate=retry_definition.get("backoff_rate"),
        interval=retry_definition.get("interval_seconds"),
        max_attempts=retry_definition.get("max_attempts"),
        errors=["SageMaker.AmazonSageMakerException"],
    )

    tags_str = stack.make_tag_str()
    tag_model = aws_lambda.Function(
        stack,
        f"tagModel{model_name}{index}",
        code=Code.from_inline(
            textwrap.dedent(
                f"""
                import boto3
                from botocore.exceptions import ClientError
                import logging
                logger = logging.getLogger()
                logger.setLevel(logging.INFO)

                sagemaker = boto3.client('sagemaker')
                def handler(event, context):
                    logger.info(f"Received Event {{event}}")
                    response = sagemaker.describe_model(
                        ModelName=event["model_name"]
                    )
                    model_arn = response["ModelArn"]
                    sagemaker.add_tags(ResourceArn=model_arn,
                                       Tags=[ {tags_str}])
                    return model_arn
                """
            )
        ),
        handler="index.handler",
        role=iam.Role.from_role_arn(
            stack,
            f"tagmodel{index}-{model_name}",
            stack.pipeline_iam_role_arn,
            mutable=False,
        ),
        runtime=aws_lambda.Runtime.PYTHON_3_7,
    )
    tag_model_task = tasks.LambdaInvoke(
        stack,
        f"Lambda: Tag Model {job['name']}",
        lambda_function=tag_model,
        payload=delete_payload,
        payload_response_only=True,
        result_path=stepfunctions.JsonPath.DISCARD,
    )

    chain = delete_model_task.next(task_create_model)
    t = chain.next(tag_model_task)
    return t
