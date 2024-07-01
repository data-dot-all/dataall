import json
import logging
import os
import random
import string

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))
log = logging.getLogger(__name__)


def shuffle_password(pwd):
    chars = list(pwd)
    random.shuffle(chars)
    return ''.join(chars)


def setup_cognito(
    region,
    resource_prefix,
    envname,
    enable_cw_canaries='False',
    with_approval_tests='False',
):
    ssm = boto3.client('ssm', region_name=region)
    user_pool_id = ssm.get_parameter(Name=f'/dataall/{envname}/cognito/userpool')['Parameter']['Value']
    log.info(f'Cognito Pool ID: {user_pool_id}')
    cognito = boto3.client('cognito-idp', region_name=region)

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
        testdata = json.loads(
            ssm.get_parameter(Name=os.path.join('/dataall', envname, 'testdata'))['Parameter']['Value']
        )
        for user_data in testdata['users'].values():
            create_user(cognito, user_pool_id, user_data['username'], user_data['password'], user_data['groups'])


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


def handler(event, context) -> None:
    log.info('Starting Cognito Configuration...')
    envname = os.environ.get('envname')
    region = os.environ.get('deployment_region')
    enable_cw_canaries = os.environ.get('enable_cw_canaries')
    resource_prefix = os.environ.get('resource_prefix')
    with_approval_tests = os.environ.get('with_approval_tests')
    setup_cognito(
        region,
        resource_prefix,
        envname,
        enable_cw_canaries,
        with_approval_tests,
    )
    log.info('Cognito Configuration Finished Successfully')
