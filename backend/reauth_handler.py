# import json
import logging
import os
from argparse import Namespace
from time import perf_counter

from dataall.core.permissions.db.tenant_policy_repositories import TenantPolicy
from dataall.base.db import get_engine
# from dataall.base.loader import load_modules, ImportMode

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))
log = logging.getLogger(__name__)

for name in ['boto3', 's3transfer', 'botocore', 'boto']:
    logging.getLogger(name).setLevel(logging.ERROR)

ENVNAME = os.environ.get('envname', 'local')
TTL = int(os.environ.get('TTL', '5'))
ENGINE = get_engine(envname=ENVNAME)


def handler(event, context):
    log.info('Lambda Event %s', event)
    log.debug('Env name %s', ENVNAME)
    log.debug('Engine %s', ENGINE.engine.url)

    # EVENT
    # {
    #   "version": "1",
    #   "region": "us-east-1",
    #   "userPoolId": "us-east-1_WkVY0Rwq6",
    #   "userName": "UserA",
    #   "callerContext": {
    #     "awsSdkVersion": "aws-sdk-unknown-unknown",
    #     "clientId": "1lmbpko39tbkdatoob5chcssqg"
    #   },
    #   "triggerSource": "PostAuthentication_Authentication",
    #   "request": {
    #     "userAttributes": {
    #       "sub": "54c814c8-1051-70c7-a364-e8edeb9040ad",
    #       "cognito:email_alias": "noahpaig+usera@amazon.com",
    #       "cognito:user_status": "CONFIRMED",
    #       "email_verified": "true",
    #       "email": "noahpaig+usera@amazon.com"
    #     },
    #     "newDeviceUsed": False
    #   },
    #   "response": {}
    # }
    try:
        data = {
            "email": event['request']['userAttributes']['email'],
            "clientId": event['callerContext']['clientId'],
            "userName": event['userName'],
            "userPoolId": event['userPoolId'],
            "ttl": TTL
        }
        with ENGINE.scoped_session() as session:
            reauth_session = TenantPolicy.update_reauth_session(session, data)
            print(reauth_session)
    except Exception as e:
        log.info(f'Error Updating ReAuth Session for User: {event.get("userName", "None")}')

    return event
