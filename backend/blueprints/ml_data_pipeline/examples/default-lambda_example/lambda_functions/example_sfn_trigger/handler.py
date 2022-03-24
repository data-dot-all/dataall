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


def make_config(timestamp, stage, bucket):
    """Creates configuration of step function input for Cannes Festival"
    Parameters
        timestamp the timestamp of execution
        stage the stage of the execution
        bucket bucket name
    """
    config = {}

    # Build lambda event input
    config["bucketName"] = bucket
    config["key"] = "examples/data/cannes/cannes_winner.csv"
    #insert your value, it can come from several places such as SSM, Databases, it depends on the use case

    return config


def handler(event, context):
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    config = make_config(timestamp, STAGE, PIPELINE_BUCKET)
    sfn_client = boto3.client("stepfunctions")

    response = sfn_client.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        name=f"example-pipeline-{timestamp}",
        input=json.dumps(config),
    )
    print(response)
    return {"statusCode": 200, "body": json.dumps("Success execution!")}
