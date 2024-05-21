import json
import logging
import os
import random
import string
import sys

import boto3
from botocore.exceptions import ClientError

logging.basicConfig(stream=sys.stdout, level=os.environ.get('LOG_LEVEL', 'INFO'))
log = logging.getLogger(os.path.basename(__file__))


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
    with_approval_tests='False',
):
    ssm = boto3.client('ssm', region_name=region)
    user_pool_id = ssm.get_parameter(Name=f'/dataall/{envname}/cognito/userpool')['Parameter']['Value']
    log.info(f'Cognito Pool ID: {user_pool_id}')
    app_client = ssm.get_parameter(Name=f'/dataall/{envname}/cognito/appclient')['Parameter']['Value']

    if custom_domain == 'False' and internet_facing == 'True':
        log.info('Switching to us-east-1 region...')
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

    log.info(f'UI: {signin_singout_link}')
    log.info(f'USERGUIDE: {user_guide_link}')

    cognito = boto3.client('cognito-idp', region_name=region)
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
    log.info(f'Updated CallBackUrls: {updated_callbacks}')

    config_logout_urls = [f'https://{signin_singout_link}']
    existing_logout_urls = user_pool['UserPoolClient'].get('LogoutURLs', [])
    updated_logout_urls = existing_logout_urls + list(set(config_logout_urls) - set(existing_logout_urls))
    log.info(f'Updated LogOutUrls: {updated_logout_urls}')

    user_pool['UserPoolClient']['CallbackURLs'] = updated_callbacks
    user_pool['UserPoolClient']['LogoutURLs'] = updated_logout_urls

    response = cognito.update_user_pool_client(
        **user_pool['UserPoolClient'],
    )

    log.info(f'CallbackUrls and LogOutUrls updated successfully: {response}')

    try:
        response = cognito.create_group(
            GroupName='DAAdministrators',
            UserPoolId=user_pool_id,
            Description='administrators group',
        )
        log.info(f'Administrators group created Successfully...: {response}')
    except ClientError as e:
        if 'GroupExistsException' in str(e):
            log.info('Group already exists')
        else:
            raise e

    if enable_cw_canaries == 'True':
        sm = boto3.client('secretsmanager', region_name=region)
        secret = sm.get_secret_value(SecretId=f'{resource_prefix}-{envname}-cognito-canary-user')
        creds = json.loads(secret['SecretString'])
        create_user(cognito, user_pool_id, creds['username'], creds['password'], ['CWCanaries'])

    if with_approval_tests == 'True':
        ssm = boto3.client('ssm', region_name=region)
        users = json.loads(
            ssm.get_parameter(Name=os.path.join('/dataall', envname, 'cognito-test-users'))['Parameter']['Value']
        )
        for username, data in users.items():
            create_user(cognito, user_pool_id, username, data['password'], data['groups'])


def create_user(cognito, user_pool_id, username, password, groups=[]):
    log.info('Creating  user...')
    try:
        response = cognito.admin_create_user(
            UserPoolId=user_pool_id,
            Username=username,
            UserAttributes=[{'Name': 'email', 'Value': f'{username}@amazonaws.com'}],
            TemporaryPassword='da@'
            + shuffle_password(
                random.SystemRandom().choice(string.ascii_uppercase)
                + random.SystemRandom().choice(string.digits)
                + ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(11))
            ),
            MessageAction='SUPPRESS',
        )
        log.info(f'User Created Successfully...: {response}')
    except ClientError as e:
        if 'UsernameExistsException' in str(e):
            log.info('User already exists')
        else:
            raise e

    log.info('Updating user password...')
    response = cognito.admin_set_user_password(
        UserPoolId=user_pool_id,
        Username=username,
        Password=password,
        Permanent=True,
    )
    log.info(f'User password updated Successfully...: {response}')

    for group in groups:
        try:
            response = cognito.create_group(
                GroupName=group,
                UserPoolId=user_pool_id,
            )
            log.info(f'Group created Successfully...: {response}')
        except ClientError as e:
            if 'GroupExistsException' in str(e):
                log.info('Group already exists')
            else:
                raise e

        response = cognito.admin_add_user_to_group(GroupName=group, UserPoolId=user_pool_id, Username=username)
        log.info(f'User added to group Successfully...: {response}')


if __name__ == '__main__':
    log.info('Starting Cognito Configuration...')
    envname = os.environ.get('envname')
    region = os.environ.get('deployment_region')
    internet_facing = os.environ.get('internet_facing')
    custom_domain = os.environ.get('custom_domain')
    enable_cw_canaries = os.environ.get('enable_cw_canaries')
    resource_prefix = os.environ.get('resource_prefix')
    with_approval_tests = os.environ.get('with_approval_tests')
    setup_cognito(
        region,
        resource_prefix,
        envname,
        internet_facing,
        custom_domain,
        enable_cw_canaries,
        with_approval_tests,
    )
    log.info('Cognito Configuration Finished Successfully')
