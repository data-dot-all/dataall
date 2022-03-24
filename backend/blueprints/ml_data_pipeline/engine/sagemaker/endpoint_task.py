import textwrap

from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda
from aws_cdk import aws_stepfunctions as stepfunctions
from aws_cdk import aws_stepfunctions_tasks as tasks
from aws_cdk import core
from aws_cdk.aws_lambda import Code
from aws_cdk.aws_stepfunctions import Choice, Condition, Pass, Wait, WaitTime

from engine.sagemaker.mappers.sm_endpoint_mapper import SageMakerEndpointPropsMapper


def make_sagemaker_endpoint_task(stack, job, group_index, job_index):
    """Creates an end point. Before creating, the function checks if the endpoint exists. If the end point already existed
    then the function deletes it first. Then, finally the end point creation takes place.

    Parameters
        stack
        job the job configuration
        group_index the group index of the end point creation task in the step function.
        job_index the job index of the end point creation task in the step function.

    Only one product variant is supported at this version.
    """
    index = f"{group_index}|{job_index}"
    verify_endpoint = aws_lambda.Function(
        stack,
        f"verifyEndpoint{index}",
        code=Code.from_inline(
            textwrap.dedent(
                """
            import boto3
            import time
            from botocore.exceptions import ClientError
            sagemaker = boto3.client('sagemaker')
            def handler(event, context):
                print("Received Event", event)
                try:
                    response = sagemaker.describe_endpoint(
                      EndpointName=event["endpoint_name"]
                    )
                    endpoint_exists = True
                    if response and (response.get("EndpointStatus") == "Failed" or 
                        response.get("EndpointStatus") == "OutOfService"
                    ):
                        response = sagemaker.delete_endpoint(
                            EndpointName=event["endpoint_name"]
                        )
                        time.sleep(30)
                        endpoint_exists = False
                    elif response and response.get("EndpointStatus") != "InService":
                        endpoint_exists = "None"
                except ClientError as e:
                    print("Endpoint does not exist", e)
                    endpoint_exists = False
                return endpoint_exists
            """
            )
        ),
        handler="index.handler",
        role=iam.Role.from_role_arn(
            stack,
            f"verifyendpointrole{index}",
            stack.pipeline_iam_role_arn,
            mutable=False,
        ),
        runtime=aws_lambda.Runtime.PYTHON_3_7,
        timeout=core.Duration.seconds(5 * 60),
    )
    stack.set_resource_tags(verify_endpoint)

    if job.get("endpoint"):
        payload = stepfunctions.TaskInput.from_object(
            {"endpoint_name.$": job["endpoint"] + ".name"}
        )
    else:
        payload = stepfunctions.TaskInput.from_text(job["name"])

    verify_endpoint_task = tasks.LambdaInvoke(
        stack,
        f"Lambda: Verify Endpoint {job['name']} Exists",
        lambda_function=verify_endpoint,
        payload=payload,
        payload_response_only=True,
        result_path="$.endpoint_exists",
    )

    endpoint_ref = (
        stepfunctions.TaskInput.from_data_at(job["endpoint"] + ".name").value
        if job.get("endpoint")
        else job["name"]
    )
    endpoint_cfg_ref = (
        stepfunctions.TaskInput.from_data_at(job["endpoint"] + ".config_name").value
        if job.get("endpoint")
        else job["config"].get("endpoint_config_name")
    )
    task_create_endpoint = tasks.SageMakerCreateEndpoint(
        stack,
        "SageMaker: Create Endpoint " + job["name"],
        **SageMakerEndpointPropsMapper.map_props(
            endpoint_ref,
            endpoint_cfg_ref,
            job.get("config", {}),
        ),
    )
    stack.set_resource_tags(task_create_endpoint)

    task_update_endpoint = tasks.SageMakerUpdateEndpoint(
        stack,
        "SageMaker: Update Endpoint " + job["name"],
        **SageMakerEndpointPropsMapper.map_props(
            endpoint_ref,
            endpoint_cfg_ref,
            job.get("config", {}),
        ),
    )

    get_endpoint_status = aws_lambda.Function(
        stack,
        f"getEndpointStatus{index}",
        code=Code.from_inline(
            textwrap.dedent(
                """
            import boto3
            from botocore.exceptions import ClientError
            sagemaker = boto3.client('sagemaker')
            def handler(event, context):
                print("Received Event", event)
                retry_count =  event["retry_count"] or event["initial_retry_count"]
                response = sagemaker.describe_endpoint(
                      EndpointName=event["endpoint_name"]
                    )
                print("End point status: ", response.get("EndpointStatus"))
                print("retry_count: ", retry_count)
                if response.get("EndpointStatus") == "InService":
                    return {
                            "status": "InService",
                            "retry_count": 0,
                    }
                else:
                    if retry_count == 1:
                        raise Exception("Too many retry")
                    return {
                            "status": response.get("EndpointStatus"),
                            "retry_count" : retry_count - 1
                        }
            """
            )
        ),
        handler="index.handler",
        role=iam.Role.from_role_arn(
            stack,
            f"getnendpointstatusrole{index}",
            stack.pipeline_iam_role_arn,
            mutable=False,
        ),
        runtime=aws_lambda.Runtime.PYTHON_3_7,
        timeout=core.Duration.seconds(15),
    )

    tags_str = stepfunctions.TaskInput.from_data_at("$.job_names.tags").value
    tag_model = aws_lambda.Function(
        stack,
        f"tagEndpoint{index}",
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
                    response = sagemaker.describe_endpoint(
                      EndpointName=event["endpoint_name"]
                    )
                    endpoint_arn = response["EndpointArn"]
                    sagemaker.add_tags(ResourceArn=endpoint_arn,
                                       Tags=[ {tags_str}])
                    return  endpoint_arn
                """
            )
        ),
        handler="index.handler",
        role=iam.Role.from_role_arn(
            stack, f"tagendpoint{index}", stack.pipeline_iam_role_arn, mutable=False
        ),
        runtime=aws_lambda.Runtime.PYTHON_3_7,
    )
    tag_model_task = tasks.LambdaInvoke(
        stack,
        f"Lambda: Tag Model {job['name']}",
        lambda_function=tag_model,
        payload=payload,
        payload_response_only=True,
        result_path=stepfunctions.JsonPath.DISCARD,
    )

    if job.get("config") and job.get("config").get(
        "wait_for_completion", ""
    ).lower() in ["y", "true"]:
        endpoint_status_path = "$.endpoint_creation_status"
        cfg = job.get("config")

        if job.get("endpoint"):
            if cfg.get("retry_count"):
                payload = stepfunctions.TaskInput.from_object(
                    {
                        "endpoint_name.$": job["endpoint"] + ".name",
                        "retry_count": cfg.get("retry_count"),
                    }
                )
            else:
                payload = stepfunctions.TaskInput.from_object(
                    {
                        "endpoint_name.$": job["endpoint"] + ".name",
                        "retry_count.$": f"{endpoint_status_path}.retry_count",
                    }
                )
        else:
            if cfg.get("retry_count"):
                payload = stepfunctions.TaskInput.from_object(
                    {
                        "endpoint_name": job["name"],
                        "retry_count": cfg.get("retry_count"),
                    }
                )
            else:
                payload = stepfunctions.TaskInput.from_object(
                    {
                        "endpoint_name": job["name"],
                        "retry_count.$": f"{endpoint_status_path}.retry_count",
                    }
                )

        get_endpoint_status_task = tasks.LambdaInvoke(
            stack,
            f"Lambda: Get Endpoint Status {job['name']}",
            lambda_function=get_endpoint_status,
            payload=payload,
            payload_response_only=True,
            result_path=endpoint_status_path,
        )

        wait_task = Wait(
            stack,
            "Wait " + job["name"],
            time=WaitTime.duration(core.Duration.seconds(15)),
        ).next(get_endpoint_status_task)

        get_endpoint_status_task.next(
            Choice(stack, f"Choice: EndPoint {job['name']} InService?")
            .when(
                Condition.string_equals(endpoint_status_path + ".status", "InService"),
                tag_model_task,
            )
            .when(
                Condition.and_(
                    Condition.number_greater_than_equals(
                        endpoint_status_path + ".retry_count", 1
                    ),
                    Condition.not_(
                        Condition.string_equals(
                            endpoint_status_path + ".status", "InService"
                        )
                    ),
                ),
                wait_task,
            )
            .otherwise(tag_model_task)
        )

        task = verify_endpoint_task.next(
            Choice(stack, f"Choice: Endpoint {job['name']} Exists?")
            .when(
                Condition.boolean_equals("$.endpoint_exists", True),
                task_update_endpoint.next(get_endpoint_status_task),
            )
            .when(
                Condition.boolean_equals("$.endpoint_exists", False),
                task_create_endpoint.next(get_endpoint_status_task),
            )
            .when(
                Condition.string_equals("$.endpoint_exists", "None"),
                stepfunctions.Pass(
                    stack, f"Pass: Endpoint {job['name']} Inconsistent Status"
                ),
            )
        )
    else:
        task = verify_endpoint_task.next(
            Choice(stack, f"Choice: Endpoint {job['name']} Exists?")
            .when(
                Condition.boolean_equals("$.endpoint_exists", True),
                task_update_endpoint.next(tag_model_task),
            )
            .when(
                Condition.boolean_equals("$.endpoint_exists", False),
                task_create_endpoint.next(tag_model_task),
            )
            .when(
                Condition.string_equals("$.endpoint_exists", "None"),
                stepfunctions.Pass(
                    stack, f"Pass: Endpoint {job['name']} Inconsistent Status"
                ),
            )
        )
    return [task, [tag_model_task]]
