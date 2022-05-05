import boto3
import pandas as pd

s3 = boto3.client("s3")


def handler(event, context):
    print("Received event", event)

    obj = s3.get_object(Bucket=event["bucketName"], Key=event["key"])
    print(obj)
