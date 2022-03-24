""" The lambdafx that triggers the execution of state machine of NNQ pipeline.
    The lambdafx builds the configuration of the state machine.
"""
import boto3
from datetime import datetime
import json
import os


# The state machine ARN. The ARN is provided in the environment variable
STATE_MACHINE_ARN = os.environ.get("PIPELINE_STATE_MACHINE_ARN")
PIPELINE_BUCKET = os.environ.get("PIPELINE_BUCKET")
STAGE = os.environ.get("PIPELINE_STAGE")


def make_config(bucket, is_first_run):
    """Creates configuration of step function input for NNQ"
    Parameters
        timestamp the timestamp of execution
        stage the stage of the execution
        bucket bucket name
    """
    config = {}
    config["pipelineBucket"] = bucket
    config["isFirstRunAfterDeploy"] = is_first_run

    return config


def handler(event, context):
    sfn_client = boto3.client("stepfunctions")

    #parse event
    print(str(event))
    if ('"state":"SUCCEEDED","stage":"DeployTestStage"' in str(event)):
        is_first_run = True
    else:
        is_first_run = False
    print(is_first_run)

    #Make step function configuration
    config = make_config(PIPELINE_BUCKET, is_first_run)
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    #Start Step function
    response = sfn_client.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        name=f"AthenaModel-{timestamp}",
        input=json.dumps(config),
    )
    print(response)
    return {"statusCode": 200, "body": json.dumps("Success execution!")}
