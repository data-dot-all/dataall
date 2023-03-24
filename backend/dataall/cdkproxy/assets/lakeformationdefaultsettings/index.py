import os
import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))
log = logging.getLogger(__name__)

AWS_ACCOUNT = os.environ.get('AWS_ACCOUNT')
AWS_REGION = os.environ.get('AWS_REGION')
lf_client = boto3.client("lakeformation", region_name=os.environ.get("AWS_REGION"))
iam_client = boto3.client('iam')


def clean_props(**props):
    data = {k: props[k] for k in props.keys() if k != 'ServiceToken'}
    return data


def validate_principals(principals):
    validated_principals = []
    for principal in principals:
        if ":role/" in principal:
            log.info(f'Principal {principal} is an IAM role, validating....')
            try:
                iam_client.get_role(RoleName=principal.split("/")[-1])
                log.info(f'Adding principal {principal} to validated principals')
                validated_principals.append(principal)
            except Exception as e:
                log.exception(f'Failed to get role {principal} due to: {e}')
                raise Exception(f'Failed to get role {principal} due to: {e}')
    return validated_principals


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
    """"Adds the PivotRole to the existing Data Lake Administrators
    Before adding any principal, it validates it exists if it is an IAM role
    """
    props = clean_props(**event['ResourceProperties'])
    try:
        response = lf_client.get_data_lake_settings(CatalogId=AWS_ACCOUNT)
        existing_admins = response.get('DataLakeSettings', {}).get('DataLakeAdmins', [])
        if existing_admins:
            existing_admins = [
                admin['DataLakePrincipalIdentifier'] for admin in existing_admins
            ]

        new_admins = props.get('DataLakeAdmins', [])
        new_admins.extend(existing_admins or [])
        validated_new_admins = validate_principals(new_admins)

        response = lf_client.put_data_lake_settings(
            CatalogId=AWS_ACCOUNT,
            DataLakeSettings={
                'DataLakeAdmins': [
                    {'DataLakePrincipalIdentifier': principal}
                    for principal in validated_new_admins
                ]
            },
        )
        log.info(f'Successfully configured AWS LakeFormation data lake admins: {validated_new_admins}| {response}')

    except ClientError as e:
        log.exception(f'Failed to setup AWS LakeFormation data lake admins due to: {e}')
        raise Exception(f'Failed to setup AWS LakeFormation data lake admins due to: {e}')

    return {
        'PhysicalResourceId': f'LakeFormationDefaultSettings{AWS_ACCOUNT}{AWS_REGION}'
    }


def on_update(event):
    return on_create(event)


def on_delete(event):
    """"Removes the PivotRole from the existing Data Lake Administrators
    Before adding any principal, it validates it exists if it is an IAM role
    """
    props = clean_props(**event['ResourceProperties'])
    try:
        response = lf_client.get_data_lake_settings(CatalogId=AWS_ACCOUNT)
        existing_admins = response.get('DataLakeSettings', {}).get('DataLakeAdmins', [])
        if existing_admins:
            existing_admins = [
                admin['DataLakePrincipalIdentifier'] for admin in existing_admins
            ]

        added_admins = props.get('DataLakeAdmins', [])
        for added_admin in added_admins:
            existing_admins.remove(added_admin)

        validated_new_admins = validate_principals(existing_admins)
        response = lf_client.put_data_lake_settings(
            CatalogId=AWS_ACCOUNT,
            DataLakeSettings={
                'DataLakeAdmins': [
                    {'DataLakePrincipalIdentifier': principal}
                    for principal in validated_new_admins
                ]
            },
        )
        log.info(f'Successfully configured AWS LakeFormation data lake admins: {validated_new_admins}| {response}')

    except ClientError as e:
        log.exception(f'Failed to setup AWS LakeFormation data lake admins due to: {e}')
        raise Exception(f'Failed to setup AWS LakeFormation data lake admins due to: {e}')

    return {
        'PhysicalResourceId': f'LakeFormationDefaultSettings{AWS_ACCOUNT}{AWS_REGION}'
    }
