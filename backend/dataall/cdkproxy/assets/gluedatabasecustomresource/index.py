import os
import json
import boto3
from botocore.exceptions import ClientError
import uuid
import logging

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))
log = logging.getLogger(__name__)

AWS_ACCOUNT = os.environ.get('AWS_ACCOUNT')
AWS_REGION = os.environ.get('AWS_REGION')
DEFAULT_ENV_ROLE_ARN = os.environ.get('DEFAULT_ENV_ROLE_ARN')
DEFAULT_CDK_ROLE_ARN = os.environ.get('DEFAULT_CDK_ROLE_ARN')

glue_client = boto3.client('glue', region_name=AWS_REGION)
lf_client = boto3.client('lakeformation', region_name=AWS_REGION)
lambda_client = boto3.client("lambda", region_name=os.environ.get("AWS_REGION"))


def clean_props(**props):
    data = {k: props[k] for k in props.keys() if k != 'ServiceToken'}
    return data


def lambda_policy_remove_duplicates(props):
    log.info(f"Removing unnecessary Lambda policy statements from Lambda: {props['LambdaArn']}")
    response = lambda_client.get_policy(FunctionName=props["LambdaArn"])
    policy = json.loads(response.get("Policy"))
    log.info(f"Lambda Policy statements:{policy.get('Statement')}")

    for statement in policy.get("Statement")[:-1]:
        log.info(f"Removing statement {statement.get('Sid')}....")
        try:
            lambda_client.remove_permission(FunctionName=props["LambdaArn"], StatementId=statement.get("Sid"))
        except ClientError as e:
            log.exception(f"Could not remove Lambda policy statement: {statement.get('Sid')}")
            raise Exception(f"Could not remove Lambda policy statement: {statement.get('Sid')} , received {str(e)}")

    response = lambda_client.get_policy(FunctionName=props["LambdaArn"])
    policy = json.loads(response.get("Policy"))
    log.info(f"Resulting Lambda policy: {policy}")


def on_event(event, context):

    request_type = event['RequestType']
    if request_type == 'Create':
        return on_create(event)
    if request_type == 'Update':
        return on_update(event)
    if request_type == 'Delete':
        return on_delete(event)
    raise Exception('Invalid request type: %s' % request_type)


def on_create(event):
    """Avoids Lambda policy size limitations by removing duplicated statements in the original Lambda policy.
    These are added automatically by the Custom Resource provider at Dataset creation.
    Creates if it does not exist Glue database for the data.all Dataset
    Grants permissions to Database Administrators = dataset Admin team IAM role, pivotRole, dataset IAM role
    """
    props = clean_props(**event['ResourceProperties'])
    log.info('Create new resource with props %s' % props)

    lambda_policy_remove_duplicates(props)

    exists = False
    try:
        glue_client.get_database(Name=props['DatabaseInput']['Name'])
        exists = True
    except ClientError as e:
        pass

    if not exists:
        try:
            response = glue_client.create_database(
                CatalogId=props.get('CatalogId'),
                DatabaseInput=props.get('DatabaseInput'),
            )
        except ClientError as e:
            log.exception(f"Could not create Glue Database {props['DatabaseInput']['Name']} in aws://{AWS_ACCOUNT}/{AWS_REGION}, received {str(e)}")
            raise Exception(f"Could not create Glue Database {props['DatabaseInput']['Name']} in aws://{AWS_ACCOUNT}/{AWS_REGION}, received {str(e)}")

    Entries = []
    for i, role_arn in enumerate(props.get('DatabaseAdministrators')):
        Entries.append(
            {
                'Id': str(uuid.uuid4()),
                'Principal': {'DataLakePrincipalIdentifier': role_arn},
                'Resource': {
                    'Database': {
                        # 'CatalogId': AWS_ACCOUNT,
                        'Name': props['DatabaseInput']['Name']
                    }
                },
                'Permissions': [
                    'Alter'.upper(),
                    'Create_table'.upper(),
                    'Drop'.upper(),
                    'Describe'.upper(),
                ],
                'PermissionsWithGrantOption': [
                    'Alter'.upper(),
                    'Create_table'.upper(),
                    'Drop'.upper(),
                    'Describe'.upper(),
                ],
            }
        )
        Entries.append(
            {
                'Id': str(uuid.uuid4()),
                'Principal': {'DataLakePrincipalIdentifier': role_arn},
                'Resource': {
                    'Table': {
                        'DatabaseName': props['DatabaseInput']['Name'],
                        'TableWildcard': {},
                        'CatalogId': props.get('CatalogId'),
                    }
                },
                'Permissions': ['SELECT', 'ALTER', 'DESCRIBE'],
                'PermissionsWithGrantOption': ['SELECT', 'ALTER', 'DESCRIBE'],
            }
        )
    lf_client.batch_grant_permissions(CatalogId=props['CatalogId'], Entries=Entries)
    physical_id = props['DatabaseInput']['Name']

    return {'PhysicalResourceId': physical_id}


def on_update(event):
    return on_create(event)


def on_delete(event):
    """ Deletes the created Glue database.
    With this action, Lake Formation permissions are also deleted.
    """
    physical_id = event['PhysicalResourceId']
    log.info('delete resource %s' % physical_id)
    try:
        glue_client.get_database(Name=physical_id)
    except ClientError as e:
        log.exception(f'Resource {physical_id} does not exists')
        raise Exception(f'Resource {physical_id} does not exists')

    try:
        response = glue_client.delete_database(CatalogId=AWS_ACCOUNT, Name=physical_id)
        log.info(f'Successfully deleted database {physical_id} in aws://{AWS_ACCOUNT}/{AWS_REGION}')
    except ClientError as e:
        log.exception(f'Could not delete databse {physical_id} in aws://{AWS_ACCOUNT}/{AWS_REGION}')
        raise Exception(f'Could not delete databse {physical_id} in aws://{AWS_ACCOUNT}/{AWS_REGION}')
