from ...db import models
from .sts import SessionHelper


def run_pipeline(state_machine_name, env: models.Environment, stage="Test"):
    if not state_machine_name:
        raise Exception("An error occurred (StackNotFound) when calling the RUN PIPELINE operation")
    aws = SessionHelper.remote_session(env.AwsAccountId)
    client = aws.client("stepfunctions", region_name=env.region)
    arn = f"arn:aws:states:{env.region}:{env.AwsAccountId}:stateMachine:{state_machine_name}"
    try:
        client.describe_state_machine(stateMachineArn=arn)
    except client.exceptions.StateMachineDoesNotExist:
        raise Exception(f"An error occurred (StateMachineNotFound) {arn} when calling the RUN PIPELINE operation")

    response = client.start_execution(stateMachineArn=arn)
    print(response)
    return response["executionArn"]


def list_executions(state_machine_name, env: models.Environment, stage="Test"):
    if not state_machine_name:
        raise Exception("An error occurred (StackNotFound) when calling the RUN PIPELINE operation")
    aws = SessionHelper.remote_session(env.AwsAccountId)
    client = aws.client("stepfunctions", region_name=env.region)
    arn = f"arn:aws:states:{env.region}:{env.AwsAccountId}:stateMachine:{state_machine_name}"
    try:
        client.describe_state_machine(stateMachineArn=arn)
    except client.exceptions.StateMachineDoesNotExist:
        print(f"An error occurred (StateMachineNotFound) {arn} when calling the RUN PIPELINE operation")
        return []
    response = client.list_executions(stateMachineArn=arn, maxResults=100)
    executions = response.get("executions", [])
    return executions
