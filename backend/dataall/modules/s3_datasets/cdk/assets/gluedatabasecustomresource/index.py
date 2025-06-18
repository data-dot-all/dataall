import os
import boto3
from botocore.exceptions import ClientError
import uuid
import logging

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))
log = logging.getLogger(__name__)

AWS_ACCOUNT = os.environ.get('AWS_ACCOUNT')
AWS_REGION = os.environ.get('AWS_REGION')
DEFAULT_ENV_ROLE_ARN = os.environ.get('DEFAULT_ENV_ROLE_ARN')
DEFAULT_CDK_ROLE_ARN = os.environ.get('DEFAULT_CDK_ROLE_ARN')

glue_client = boto3.client('glue', region_name=AWS_REGION)
lf_client = boto3.client('lakeformation', region_name=AWS_REGION)


def clean_props(**props):
    data = {k: props[k] for k in props.keys() if k != 'ServiceToken'}
    return data


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
    """Creates if it does not exist Glue database for the data.all Dataset
    Grants permissions to Database Administrators = dataset Admin team IAM role, pivotRole, dataset IAM role
    """
    props = clean_props(**event['ResourceProperties'])
    log.info('Create new resource with props %s' % props)

    exists = False
    try:
        glue_client.get_database(Name=props['DatabaseInput']['Name'])
        exists = True
    except ClientError:
        pass

    if not exists:
        try:
            db_input = props.get('DatabaseInput').copy()
            if 'Imported' in db_input:
                del db_input['Imported']
            response = glue_client.create_database(
                CatalogId=props.get('CatalogId'),
                DatabaseInput=db_input,
            )
        except ClientError as e:
            log.exception(
                f'Could not create Glue Database {props["DatabaseInput"]["Name"]} in aws://{AWS_ACCOUNT}/{AWS_REGION}, received {str(e)}'
            )
            raise Exception(
                f'Could not create Glue Database {props["DatabaseInput"]["Name"]} in aws://{AWS_ACCOUNT}/{AWS_REGION}, received {str(e)}'
            )

    Entries = []
    for i, role_arn in enumerate(props.get('DatabaseAdministrators', [])):
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

        default_db_exists = False
        try:
            glue_client.get_database(Name='default')
            default_db_exists = True
        except ClientError as e:
            log.exception(f'Failed to get default glue database due to: {e}')
            raise Exception(f'Failed to get default glue database due to: {e}')

        if default_db_exists:
            Entries.append(
                {
                    'Id': str(uuid.uuid4()),
                    'Principal': {'DataLakePrincipalIdentifier': role_arn},
                    'Resource': {'Database': {'Name': 'default'}},
                    'Permissions': ['Describe'.upper()],
                }
            )

    lf_client.batch_grant_permissions(CatalogId=props['CatalogId'], Entries=Entries)
    physical_id = props['DatabaseInput']['Imported'] + props['DatabaseInput']['Name']

    return {'PhysicalResourceId': physical_id}


def on_update(event):
    return on_create(event)


def on_delete(event):
    """Deletes the created Glue database.
    With this action, Lake Formation permissions are also deleted.
    Imported databases are not deleted
    """
    physical_id = event['PhysicalResourceId']
    if physical_id.startswith('IMPORTED'):
        log.info(f'Imported database {physical_id} will not be deleted (it was not created by dataa.all)')
    elif physical_id.startswith('CREATED'):
        database_name = physical_id.replace('CREATED-', '')
        log.info('delete resource %s' % database_name)
        try:
            glue_client.get_database(Name=database_name)
        except ClientError:
            log.exception(f'Resource {database_name} does not exists')
            raise Exception(f'Resource {database_name} does not exists')

        try:
            response = glue_client.delete_database(CatalogId=AWS_ACCOUNT, Name=database_name)
            log.info(f'Successfully deleted database {database_name} in aws://{AWS_ACCOUNT}/{AWS_REGION}')
        except ClientError:
            log.exception(f'Could not delete database {database_name} in aws://{AWS_ACCOUNT}/{AWS_REGION}')
            raise Exception(f'Could not delete database {database_name} in aws://{AWS_ACCOUNT}/{AWS_REGION}')
    else:
        log.info('Old PhysicalID, do not delete anything')
