""" The lambda that triggers the execution of state machine of iris classification.
    The lambda builds the configuration of the state machine.
"""
import boto3
from datetime import datetime
import json
import os


# The state machine ARN. The ARN is provided in the environment variable
# by the ML pipeline deployment.
STATE_MACHINE_ARN = os.environ.get("PIPELINE_STATE_MACHINE_ARN")
PIPELINE_BUCKET = os.environ.get("PIPELINE_BUCKET")
STAGE = os.environ.get("PIPELINE_STAGE")


def make_config(timestamp, stage, bucket, model_name, launch_ep):
    """Creates configuration of step function input for iris"
    Parameters
        timestamp the timestamp of execution
        stage the stage of the execution
        bucket bucket name
    """
    config = {}
    config["bucket"] = bucket
    # Iris.data is by default created under the pipeline bucket and the data/iris/iris.data key.
    config["key"] = "data/iris/iris.data"

    # The output of the preparation task.
    config["output_prefix"] = f"data/output/iris/{stage}/{timestamp}/prepare"

    # Build training input
    config["training_input"] = {
        "content_type": "text/csv",
        "train_s3_uri": {
            "bucket": bucket,
            "key_prefix": f"data/output/iris/{stage}/{timestamp}/prepare/training_data.csv"
        },
        "validation_s3_uri": {
            "bucket": bucket,
            "key_prefix": f"data/output/iris/{stage}/{timestamp}/prepare/validation_data.csv"
        }
    }

    config["s3_transform_input"] = f"s3://{bucket}/data/output/iris/{stage}/{timestamp}/prepare/test.csv"

    # Build training output
    config[
        "training_output"
    ] = f"s3://{bucket}/data/output/iris/{stage}/{timestamp}/training/"

    config[
        "s3_transform_output"
    ] =  f"s3://{bucket}/data/output/iris/{stage}/{timestamp}/transform/"

    config[ "s3_transform_output_path"] =  {
          "bucket": bucket, 
          "key_prefix": f"data/output/iris/{stage}/{timestamp}/transform/"
    }

    config["kpi_output_path"] = {
        "bucket" : bucket,
        "key_prefix" : f"data/output/iris/{stage}/{timestamp}/metrics/"
    }

    config["model_name"] = f"{model_name}-{timestamp}"
    config["hpo_output"] = f"s3://{bucket}/data/output/iris/{stage}/{timestamp}/hpo/"
    config["timestamp"] = timestamp
    config["launch_end_point"] = (
        (launch_ep == True) or (launch_ep.lower() in ["true", "y", "yes"])
        if launch_ep
        else False
    )

    config["transform_job_name"] = f"transform-{model_name}-{timestamp}"

    # Define end point configuration
    config["EndPoint"] = {
        "config_name": config["model_name"] + "-ep-conf",
        "name": f"iris-{stage}",
    }

    return config


def handler(event, context):
    if event.get("model_name"):
        model_name = event["model_name"]
    else:
        model_name = "iris"
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    launch_ep = event.get("with_endpoint")

    config = make_config(timestamp, STAGE, PIPELINE_BUCKET, model_name, launch_ep)
    sfn_client = boto3.client("stepfunctions")

    response = sfn_client.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        name=f"{model_name}-{timestamp}",
        input=json.dumps(config),
    )
    print(response)
    return {"statusCode": 200, "body": json.dumps("Success execution!")}
