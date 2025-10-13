import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))
log = logging.getLogger(__name__)


def setup_cognito(
    region,
    envname,
    custom_domain='False',
):
    ssm = boto3.client('ssm', region_name=region)
    user_pool_id = ssm.get_parameter(Name=f'/dataall/{envname}/cognito/userpool')['Parameter']['Value']
    log.info(f'Cognito Pool ID: {user_pool_id}')
    app_client = ssm.get_parameter(Name=f'/dataall/{envname}/cognito/appclient')['Parameter']['Value']

    if custom_domain == 'False':
        log.info('Switching to us-east-1 region...')
        ssm = boto3.client('ssm', region_name='us-east-1')
        signin_singout_link = ssm.get_parameter(Name=f'/dataall/{envname}/CloudfrontDistributionDomainName')[
            'Parameter'
        ]['Value']
    else:
        signin_singout_link = ssm.get_parameter(Name=f'/dataall/{envname}/frontend/custom_domain_name')['Parameter'][
            'Value'
        ]

    log.info(f'UI: {signin_singout_link}')

    cognito = boto3.client('cognito-idp', region_name=region)
    user_pool = cognito.describe_user_pool_client(UserPoolId=user_pool_id, ClientId=app_client)

    del user_pool['UserPoolClient']['CreationDate']
    del user_pool['UserPoolClient']['LastModifiedDate']

    config_callbacks = [
        f'https://{signin_singout_link}',
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


def handler(event, context) -> None:
    log.info('Starting Cognito Configuration...')
    envname = os.environ.get('envname')
    region = os.environ.get('deployment_region')
    custom_domain = os.environ.get('custom_domain')
    setup_cognito(
        region,
        envname,
        custom_domain,
    )
    log.info('Cognito Configuration Finished Successfully')
