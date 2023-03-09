import os
import boto3
from botocore.exceptions import ClientError


def clean_props(**props):
    data = {k: props[k] for k in props.keys() if k != 'ServiceToken'}
    return data

def validate_principals(principals):
    iam_client = boto3.client('iam')
    validated_principals = []
    for principal in principals:
        try:
            iam_client.get_role(RoleName=principal.split("/")[-1])
        except Exception as e:
            print(f'Failed to get role {principal} due to: {e}')
        validated_principals.append(principal)
    return validated_principals

def on_event(event, context):
    AWS_ACCOUNT = os.environ.get('AWS_ACCOUNT')
    AWS_REGION = os.environ.get('AWS_REGION')
    DEFAULT_ENV_ROLE_ARN = os.environ.get('DEFAULT_ENV_ROLE_ARN')

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
    """
    AWS_ACCOUNT = os.environ.get('AWS_ACCOUNT')
    AWS_REGION = os.environ.get('AWS_REGION')
    props = clean_props(**event['ResourceProperties'])
    try:
        lf_client = boto3.client('lakeformation', region_name=AWS_REGION)

        response = lf_client.get_data_lake_settings(CatalogId=AWS_ACCOUNT)

        existing_admins = response.get('DataLakeSettings', {}).get('DataLakeAdmins', [])
        if existing_admins:
            existing_admins = [
                admin['DataLakePrincipalIdentifier'] for admin in existing_admins
            ]

        new_admins = props.get('DataLakeAdmins', [])
        new_admins.extend(existing_admins or [])

        response = lf_client.put_data_lake_settings(
            CatalogId=AWS_ACCOUNT,
            DataLakeSettings={
                'DataLakeAdmins': [
                    {'DataLakePrincipalIdentifier': principal}
                    for principal in validate_principals(new_admins)
                ]
            },
        )
        print(
            f'Successfully configured AWS LakeFormation data lake admins: {validated_new_admins}| {response}'
        )
    except ClientError as e:
        print(f'Failed to setup AWS LakeFormation data lake admins due to: {e}')

    return {
        'PhysicalResourceId': f'LakeFormationDefaultSettings{AWS_ACCOUNT}{AWS_REGION}'
    }


def on_update(event):
    return on_create(event)


def on_delete(event):
    """"Removes the PivotRole to the existing Data Lake Administrators
    """
    AWS_ACCOUNT = os.environ.get('AWS_ACCOUNT')
    AWS_REGION = os.environ.get('AWS_REGION')
    props = clean_props(**event['ResourceProperties'])
    try:
        lf_client = boto3.client('lakeformation', region_name=AWS_REGION)

        response = lf_client.get_data_lake_settings(CatalogId=AWS_ACCOUNT)

        existing_admins = response.get('DataLakeSettings', {}).get('DataLakeAdmins', [])
        if existing_admins:
            existing_admins = [
                admin['DataLakePrincipalIdentifier'] for admin in existing_admins
            ]

        added_admins = props.get('DataLakeAdmins', [])
        for added_admin in added_admins:
            existing_admins.remove(added_admin)

        response = lf_client.put_data_lake_settings(
            CatalogId=AWS_ACCOUNT,
            DataLakeSettings={
                'DataLakeAdmins': [
                    {'DataLakePrincipalIdentifier': principal}
                    for principal in validate_principals(existing_admins_admins)
                ]
            },
        )
        print(
            f'Successfully configured AWS LakeFormation data lake admins: {existing_admins}| {response}'
        )
    except ClientError as e:
        print(f'Failed to setup AWS LakeFormation data lake admins due to: {e}')

    return {
        'PhysicalResourceId': f'LakeFormationDefaultSettings{AWS_ACCOUNT}{AWS_REGION}'
    }
