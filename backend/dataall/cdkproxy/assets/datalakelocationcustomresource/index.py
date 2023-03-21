import logging
import os
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
    props = event["ResourceProperties"]
    if not _is_resource_registered(props["ResourceArn"]):
        register(props)
    else:
        update(props)


def _is_resource_registered(resource_arn: str):
    lf_resources = lf_client.list_resources(FilterConditionList=[{"Field": "RESOURCE_ARN", "ComparisonOperator": "EQ", "StringValueList": [resource_arn]}])
    return len(lf_resources["ResourceInfoList"]) > 0


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
    update(event["ResourceProperties"])


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
    resource_arn = event["ResourceProperties"]["ResourceArn"]
    log.info(f"Unregistering LakeFormation Resource: {resource_arn}")
    try:
        lf_client.deregister_resource(ResourceArn=resource_arn)
    except ClientError as e:
        log.exception(f"Could not unregister LakeFormation resource: {resource_arn}")
        raise Exception(f"Could not unregister LakeFormation Resource: {resource_arn}, received {str(e)}")
