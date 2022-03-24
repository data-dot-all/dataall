import textwrap

from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_stepfunctions as stepfunctions
from aws_cdk import aws_stepfunctions_tasks as tasks
from aws_cdk.aws_lambda import Code

from engine.sagemaker.mappers.sm_endpointconfig_mapper import (
    SageMakerEndpointConfigPropsMapper,
)


def make_sagemaker_endpoint_config_task(stack, job, group_index, job_index):
    index = f"{group_index}|{job_index}"
    delete_endpoint_config = lambda_.Function(
        stack,
        f"deleteEndpointConfig{index}",
        code=Code.from_inline(
            textwrap.dedent(
                """
            import boto3
            from botocore.exceptions import ClientError
            sagemaker = boto3.client('sagemaker')
            def handler(event, context):
                print("Received Event", event)
                try:
                    response = sagemaker.describe_endpoint_config(
                      EndpointConfigName=event["endpoint_config_name"]
                    )
                    exists = True
                    if response and response.get("EndpointConfigName"):
                        response = sagemaker.delete_endpoint_config(
                          EndpointConfigName=event["endpoint_config_name"]
                        )
                        exists = False
                except ClientError as e:
                    print("Error Deleting EndpointConfig", e)
                    exists = True
                return exists
            """
            )
        ),
        handler="index.handler",
        role=iam.Role.from_role_arn(
            stack,
            f"verifyendpointconfig{index}",
            stack.pipeline_iam_role_arn,
            mutable=False,
        ),
        runtime=lambda_.Runtime.PYTHON_3_7,
    )
    delete_endpointconfig_task = tasks.LambdaInvoke(
        stack,
        f"Lambda: Delete Endpoint Config {job['name']} If exists",
        lambda_function=delete_endpoint_config,
        payload=stepfunctions.TaskInput.from_object(
            {"endpoint_config_name.$": job["endpoint"] + ".config_name"}
        ),
        payload_response_only=True,
        result_path="$.endpointconfig",
    )
    task_create_endpointconfig = tasks.SageMakerCreateEndpointConfig(
        stack,
        "SageMaker: Create Endpoint Config " + job["name"],
        **SageMakerEndpointConfigPropsMapper.map_props(
            stack,
            stepfunctions.TaskInput.from_data_at(
                job["endpoint"] + ".config_name"
            ).value,
            job["config"],
            stepfunctions.TaskInput.from_data_at(
                job["config"]["model_name_path"]
            ).value,
        ),
    )
    tags_str = stack.make_tag_str()
    tag_endpoint_config = lambda_.Function(
        stack,
        f"tagEndpointConfig{index}",
        code=Code.from_inline(
            textwrap.dedent(
                f"""
            import boto3
            from botocore.exceptions import ClientError
            sagemaker = boto3.client('sagemaker')
            def handler(event, context):
                print("Received Event", event)
                try:
                    response = sagemaker.describe_endpoint_config(
                      EndpointConfigName=event["endpoint_config_name"]
                    )
                    endpoint_config_arn = response["EndpointConfigArn"]
                    sagemaker.add_tags(ResourceArn=endpoint_config_arn,
                                       Tags=[ {tags_str}])
                    return  endpoint_config_arn

                except ClientError as e:
                    print("Error EndpointConfig", e)
                    exists = True
                return exists
            """
            )
        ),
        handler="index.handler",
        role=iam.Role.from_role_arn(
            stack,
            f"tagendpointconfig{index}",
            stack.pipeline_iam_role_arn,
            mutable=False,
        ),
        runtime=lambda_.Runtime.PYTHON_3_7,
    )
    tag_endpointconfig_task = tasks.LambdaInvoke(
        stack,
        f"Lambda: Tag Endpoint Config {job['name']}",
        lambda_function=tag_endpoint_config,
        payload=stepfunctions.TaskInput.from_object(
            {"endpoint_config_name.$": job["endpoint"] + ".config_name"}
        ),
        payload_response_only=True,
        result_path="$.endpointconfig",
    )

    task = task_create_endpointconfig.next(tag_endpointconfig_task)

    task = delete_endpointconfig_task.next(task)
    return task
