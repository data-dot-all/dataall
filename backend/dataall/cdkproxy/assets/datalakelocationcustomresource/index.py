import logging
import os
import json
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))
log = logging.getLogger(__name__)

lf_client = boto3.client("lakeformation", region_name=os.environ.get("AWS_REGION"))


def on_event(event, context):
    request_type = event["RequestType"]
    if request_type == "Create":
        return on_create(event)
    if request_type == "Update":
        return on_update(event)
    if request_type == "Delete":
        return on_delete(event)
    raise Exception(f"Invalid request type: {request_type}")


def on_create(event):
    """ Checks if the S3 location is already registered in Lake Formation.
    If already registered it updated the roleArn for the location.
    If not registered, it registers the location.
    """
    props = event["ResourceProperties"]
    if not _is_resource_registered(props["ResourceArn"]):
        register(props)
    else:
        update(props)


def _is_resource_registered(resource_arn: str):
    response = lf_client.list_resources(
        FilterConditionList=[{"Field": "RESOURCE_ARN", "ComparisonOperator": "EQ", "StringValueList": [resource_arn]}])
    lf_resources = response["ResourceInfoList"]
    while "NextToken" in response:
        response = lf_client.list_resources(
            FilterConditionList=[{"Field": "RESOURCE_ARN", "ComparisonOperator": "EQ", "StringValueList": [resource_arn]}],
            NextToken=response["NextToken"]
        )
        log.info(f"Response from listing resources with ARN {resource_arn}: {response}")
        lf_resources.extend(response["ResourceInfoList"])

    log.info(f"Full Resource list filter with ARN {resource_arn}: {lf_resources}")
    return len(lf_resources) > 0


def register(props):
    resource_arn = props["ResourceArn"]
    role_arn = props["RoleArn"]
    log.info(f"Registering LakeFormation Resource: {resource_arn} and roleArn: {role_arn}")
    try:
        lf_client.register_resource(
            ResourceArn=resource_arn,
            UseServiceLinkedRole=props["UseServiceLinkedRole"] == "True",
            RoleArn=role_arn,
        )
    except ClientError as e:
        log.exception(f"Could not register LakeFormation resource: {resource_arn}")
        raise Exception(f"Could not register LakeFormation resource: {resource_arn} , received {str(e)}")


def on_update(event):
    on_create(event)


def update(props):
    resource_arn = props["ResourceArn"]
    role_arn = props["RoleArn"]
    log.info(f"Updating LakeFormation Resource: {resource_arn} with roleArn: {role_arn}")
    try:
        lf_client.update_resource(RoleArn=role_arn, ResourceArn=resource_arn)
    except ClientError as e:
        log.exception(f"Could not update LakeFormation resource: {resource_arn}")
        raise Exception(f"Could not update LakeFormation resource: {resource_arn}, received {str(e)}")


def on_delete(event):
    """ Deregisters the S3 location from Lake Formation
    """
    resource_arn = event["ResourceProperties"]["ResourceArn"]
    log.info(f"Unregistering LakeFormation Resource: {resource_arn}")
    try:
        lf_client.deregister_resource(ResourceArn=resource_arn)
    except ClientError as e:
        log.exception(f"Could not unregister LakeFormation resource: {resource_arn}")
        raise Exception(f"Could not unregister LakeFormation Resource: {resource_arn}, received {str(e)}")
