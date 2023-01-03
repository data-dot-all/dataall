import os
import boto3
from botocore.exceptions import ClientError
import uuid


def clean_props(**props):
    data = {k: props[k] for k in props.keys() if k != 'ServiceToken'}
    return data


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
    AWS_ACCOUNT = os.environ.get('AWS_ACCOUNT')
    AWS_REGION = os.environ.get('AWS_REGION')
    props = clean_props(**event['ResourceProperties'])
    try:
        client = boto3.client('lakeformation', region_name=AWS_REGION)

        response = client.get_data_lake_settings(CatalogId=AWS_ACCOUNT)

        existing_admins = response.get('DataLakeSettings', {}).get('DataLakeAdmins', [])
        if existing_admins:
            existing_admins = [
                admin['DataLakePrincipalIdentifier'] for admin in existing_admins
            ]

        new_admins = props.get('DataLakeAdmins', [])
        new_admins.extend(existing_admins or [])

        response = client.put_data_lake_settings(
            CatalogId=AWS_ACCOUNT,
            DataLakeSettings={
                'DataLakeAdmins': [
                    {'DataLakePrincipalIdentifier': principal}
                    for principal in new_admins
                ]
            },
        )
        print(
            f'Successfully configured AWS LakeFormation data lake admins: {new_admins}| {response}'
        )
        lftags_dict = props.get('LFTags', {})
        envAdmin = props.get('EnvAdminRole', {})

        Entries = []
        for tagkey in lftags_dict:
            # Create LF Tag
            client.create_lf_tag(
                CatalogId=AWS_ACCOUNT,
                TagKey=tagkey,
                TagValues=lftags_dict[tagkey]
            )
            print(f'Successfully create LF Tag {tagkey}')

            # Add Permissions to Env Admin
            Entries.append(
                {
                    'Id': str(uuid.uuid4()),
                    'Principal': {'DataLakePrincipalIdentifier': envAdmin},
                    'Resource': {
                        'LFTag': {
                            'CatalogId': AWS_ACCOUNT,
                            'TagKey': tagkey,
                            'TagValues': lftags_dict[tagkey]
                        }
                    },
                    'Permissions': ["DESCRIBE", "ASSOCIATE"],
                    'PermissionsWithGrantOption': ["DESCRIBE", "ASSOCIATE"]
                }
            )
        client.batch_grant_permissions(CatalogId=AWS_ACCOUNT, Entries=Entries)
    except ClientError as e:
        print(f'Failed to setup AWS LakeFormation data lake admins due to: {e}')

    return {
        'PhysicalResourceId': f'LakeFormationDefaultSettings{AWS_ACCOUNT}{AWS_REGION}'
    }


def on_update(event):
    return on_create(event)


def on_delete(event):
    pass
