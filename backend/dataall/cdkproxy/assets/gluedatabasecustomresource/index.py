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
    DEFAULT_ENV_ROLE_ARN = os.environ.get('DEFAULT_ENV_ROLE_ARN')
    DEFAULT_CDK_ROLE_ARN = os.environ.get('DEFAULT_CDK_ROLE_ARN')
    props = clean_props(**event['ResourceProperties'])
    print('Create new resource with props %s' % props)
    glue = boto3.client('glue', region_name=AWS_REGION)
    lf = boto3.client('lakeformation', region_name=AWS_REGION)
    exists = False
    try:
        glue.get_database(Name=props['DatabaseInput']['Name'])
        exists = True
    except ClientError as e:
        pass

    if not exists:
        try:
            response = glue.create_database(
                CatalogId=props.get('CatalogId'),
                DatabaseInput=props.get('DatabaseInput'),
            )
        except ClientError as e:
            raise Exception(
                f"Could not create Glue Database {props['DatabaseInput']['Name']} in aws://{AWS_ACCOUNT}/{AWS_REGION}, received {str(e)}"
            )
    # Create LF Tags if Required
    if props.get("LFTags"):
        # Create LF Tag if Not Exist
        lf_tags = props.get("LFTags")
        for tagkey in lf_tags:
            try:
                lf.create_lf_tag(
                    CatalogId=AWS_ACCOUNT,
                    TagKey=tagkey,
                    TagValues=[lf_tags[tagkey]]
                )
                print(f'Successfully create LF Tag {tagkey}')
            except ClientError as e:
                print(f'LF Tag {tagkey} already exists, skippping create attempting update...')
                try:
                    lf.update_lf_tag(
                        CatalogId=AWS_ACCOUNT,
                        TagKey=tagkey,
                        TagValuesToAdd=[lf_tags[tagkey]]
                    )
                except ClientError as e:
                    print(f'LF Tag {tagkey} already has value {lf_tags[tagkey]}, skippping update...')
                    pass

            # Add Tag to Resource
            lf.add_lf_tags_to_resource(
                CatalogId=props.get('CatalogId'),
                Resource={
                    'Database': {
                        'CatalogId': props.get('CatalogId'),
                        'Name': props['DatabaseInput']['Name']
                    }
                },
                LFTags=[
                    {
                        'CatalogId': props.get('CatalogId'),
                        'TagKey': tagkey,
                        'TagValues': [lf_tags[tagkey]]
                    },
                ]
            )

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
                ],
                'PermissionsWithGrantOption': [
                    'Alter'.upper(),
                    'Create_table'.upper(),
                    'Drop'.upper(),
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
    lf.batch_grant_permissions(CatalogId=props['CatalogId'], Entries=Entries)
    physical_id = props['DatabaseInput']['Name']

    return {'PhysicalResourceId': physical_id}


def on_update(event):
    return on_create(event)


def on_delete(event):
    AWS_ACCOUNT = os.environ.get('AWS_ACCOUNT')
    AWS_REGION = os.environ.get('AWS_REGION')
    DEFAULT_ENV_ROLE_ARN = os.environ.get('DEFAULT_ENV_ROLE_ARN')
    physical_id = event['PhysicalResourceId']
    print('delete resource %s' % physical_id)
    glue = boto3.client('glue', region_name=AWS_REGION)
    try:
        glue.get_database(Name=physical_id)
    except ClientError as e:
        raise Exception(f'Resource {physical_id} does not exists')

    try:
        response = glue.delete_database(CatalogId=AWS_ACCOUNT, Name=physical_id)
        print(
            f'Successfully deleted database {physical_id} in aws://{AWS_ACCOUNT}/{AWS_REGION}'
        )
    except ClientError as e:
        raise Exception(
            f'Could not delete databse {physical_id} in aws://{AWS_ACCOUNT}/{AWS_REGION}'
        )
