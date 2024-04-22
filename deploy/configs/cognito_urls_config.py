import json
import os
import random
import string

import boto3
from botocore.exceptions import ClientError


def shuffle_password(pwd):
    chars = list(pwd)
    random.shuffle(chars)
    return ''.join(chars)


def setup_cognito(
    region,
    resource_prefix,
    envname,
    internet_facing='True',
    custom_domain='False',
    enable_cw_canaries='False',
):
    ssm = boto3.client('ssm', region_name=region)
    user_pool_id = ssm.get_parameter(Name=f'/dataall/{envname}/cognito/userpool')['Parameter']['Value']
    print(f'Cognito Pool ID: {user_pool_id}')
    app_client = ssm.get_parameter(Name=f'/dataall/{envname}/cognito/appclient')['Parameter']['Value']

    if custom_domain == 'False' and internet_facing == 'True':
        print('Switching to us-east-1 region...')
        ssm = boto3.client('ssm', region_name='us-east-1')
        signin_singout_link = ssm.get_parameter(Name=f'/dataall/{envname}/CloudfrontDistributionDomainName')[
            'Parameter'
        ]['Value']
        user_guide_link = ssm.get_parameter(
            Name=f'/dataall/{envname}/cloudfront/docs/user/CloudfrontDistributionDomainName'
        )['Parameter']['Value']
    else:
        signin_singout_link = ssm.get_parameter(Name=f'/dataall/{envname}/frontend/custom_domain_name')['Parameter'][
            'Value'
        ]
        user_guide_link = ssm.get_parameter(Name=f'/dataall/{envname}/userguide/custom_domain_name')['Parameter'][
            'Value'
        ]

    print(f'UI: {signin_singout_link}')
    print(f'USERGUIDE: {user_guide_link}')

    cognito = boto3.client('cognito-idp', region_name=region)
    try:
        user_pool = cognito.describe_user_pool_client(UserPoolId=user_pool_id, ClientId=app_client)

        del user_pool['UserPoolClient']['CreationDate']
        del user_pool['UserPoolClient']['LastModifiedDate']

        config_callbacks = [
            f'https://{signin_singout_link}',
            f'https://{user_guide_link}/parseauth',
        ]
        existing_callbacks = user_pool['UserPoolClient'].get('CallbackURLs', [])
        if 'https://example.com' in existing_callbacks:
            existing_callbacks.remove('https://example.com')
        updated_callbacks = existing_callbacks + list(set(config_callbacks) - set(existing_callbacks))
        print(f'Updated CallBackUrls: {updated_callbacks}')

        config_logout_urls = [f'https://{signin_singout_link}']
        existing_logout_urls = user_pool['UserPoolClient'].get('LogoutURLs', [])
        updated_logout_urls = existing_logout_urls + list(set(config_logout_urls) - set(existing_logout_urls))
        print(f'Updated LogOutUrls: {updated_logout_urls}')

        user_pool['UserPoolClient']['CallbackURLs'] = updated_callbacks
        user_pool['UserPoolClient']['LogoutURLs'] = updated_logout_urls

        response = cognito.update_user_pool_client(
            **user_pool['UserPoolClient'],
        )

        print(f'CallbackUrls and LogOutUrls updated successfully: {response}')

        try:
            response = cognito.create_group(
                GroupName='DAAdministrators',
                UserPoolId=user_pool_id,
                Description='administrators group',
            )
            print(f'Administrators group created Successfully...: {response}')
        except ClientError as e:
            if 'GroupExistsException' in str(e):
                print('Group already exists')
            else:
                raise e

        if enable_cw_canaries == 'True':
            sm = boto3.client('secretsmanager', region_name=region)
            secret = sm.get_secret_value(SecretId=f'{resource_prefix}-{envname}-cognito-canary-user')
            creds = json.loads(secret['SecretString'])
            username = creds['username']
            print('Creating Canaries user...')
            try:
                response = cognito.admin_create_user(
                    UserPoolId=user_pool_id,
                    Username=username,
                    UserAttributes=[{'Name': 'email', 'Value': f'{username}@amazonaws.com'}],
                    TemporaryPassword='da@'
                    + shuffle_password(
                        random.SystemRandom().choice(string.ascii_uppercase)
                        + random.SystemRandom().choice(string.digits)
                        + ''.join(
                            random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(11)
                        )
                    ),
                    MessageAction='SUPPRESS',
                )
                print(f'User Created Successfully...: {response}')
            except ClientError as e:
                if 'UsernameExistsException' in str(e):
                    print('User already exists')
                else:
                    raise e

            print('Updating Canaries user password...')
            response = cognito.admin_set_user_password(
                UserPoolId=user_pool_id,
                Username=username,
                Password=creds['password'],
                Permanent=True,
            )
            print(f'User password updated Successfully...: {response}')
            try:
                response = cognito.create_group(
                    GroupName='CWCanaries',
                    UserPoolId=user_pool_id,
                    Description='CW Canary group',
                )
                print(f'Canaries group created Successfully...: {response}')
            except ClientError as e:
                if 'GroupExistsException' in str(e):
                    print('Group already exists')
                else:
                    raise e

            response = cognito.admin_add_user_to_group(
                GroupName='CWCanaries', UserPoolId=user_pool_id, Username=username
            )
            print(f'User added to group Successfully...: {response}')

    except ClientError as e:
        print(f'Failed to setup cognito due to: {e}')
        raise e


if __name__ == '__main__':
    print('Starting Cognito Configuration...')
    envname = os.environ.get('envname')
    region = os.environ.get('deployment_region')
    internet_facing = os.environ.get('internet_facing')
    custom_domain = os.environ.get('custom_domain')
    enable_cw_canaries = os.environ.get('enable_cw_canaries')
    resource_prefix = os.environ.get('resource_prefix')
    setup_cognito(
        region,
        resource_prefix,
        envname,
        internet_facing,
        custom_domain,
        enable_cw_canaries,
    )
    print('Cognito Configuration Finished Successfully')
