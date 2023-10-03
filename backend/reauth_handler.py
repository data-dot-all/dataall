import json
import logging
import os
from argparse import Namespace
from time import perf_counter

from ariadne import (
    gql,
    graphql_sync,
)

from dataall.base.api import bootstrap as bootstrap_schema, get_executable_schema
from dataall.core.permissions.db import save_permissions_with_tenant
from dataall.core.permissions.db.tenant_policy_repositories import TenantPolicy
from dataall.base.db import get_engine
from dataall.base.loader import load_modules, ImportMode

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))
log = logging.getLogger(__name__)

start = perf_counter()
for name in ['boto3', 's3transfer', 'botocore', 'boto']:
    logging.getLogger(name).setLevel(logging.ERROR)

load_modules(modes={ImportMode.API})
SCHEMA = bootstrap_schema()
TYPE_DEFS = gql(SCHEMA.gql(with_directives=False))
ENVNAME = os.getenv('envname', 'local')
ENGINE = get_engine(envname=ENVNAME)

save_permissions_with_tenant(ENGINE)


class ReAuthException(Exception):
    """Exception raised when reAuth is required.

    Attributes:
        operationName -- input salary which caused the error
        message -- explanation of the error
    """
    def __init__(self, operationName, message="Re-Auth is Required"):
        self.operationName = operationName
        super().__init__(self.message)


def resolver_adapter(resolver):
    def adapted(obj, info, **kwargs):
        return resolver(
            context=Namespace(
                engine=info.context['engine'],
                es=info.context['es'],
                username=info.context['username'],
                groups=info.context['groups'],
                schema=info.context['schema'],
            ),
            source=obj or None,
            **kwargs,
        )

    return adapted


executable_schema = get_executable_schema()
end = perf_counter()
print(f'Lambda Context ' f'Initialization took: {end - start:.3f} sec')


def get_groups(claims):
    if not claims:
        raise ValueError(
            'Received empty claims. ' 'Please verify Cognito authorizer configuration',
            claims,
        )
    groups = list()
    saml_groups = claims.get('custom:saml.groups', '')
    if len(saml_groups):
        groups: list = (
            saml_groups.replace('[', '').replace(']', '').replace(', ', ',').split(',')
        )
    cognito_groups = claims.get('cognito:groups', '').split(',')
    groups.extend(cognito_groups)
    return groups


def handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """

    log.info('Lambda Event %s', event)
    log.debug('Env name %s', ENVNAME)
    log.debug('Engine %s', ENGINE.engine.url)

    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'content-type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': '*',
            },
        }

    if 'authorizer' in event['requestContext']:
        if 'claims' not in event['requestContext']['authorizer']:
            claims = event['requestContext']['authorizer']
        else:
            claims = event['requestContext']['authorizer']['claims']
        username = claims['email']
        log.debug('username is %s', username)
        try:
            groups = get_groups(claims)
            log.debug('groups are %s', ",".join(groups))
            with ENGINE.scoped_session() as session:
                reauth_session = TenantPolicy.create_reauth_session(session, username)
                print(reauth_session)
        except Exception as e:
            print(f'Error creating reauth session due to: {e}')
            groups = []
    else:
        raise Exception(f'Could not initialize user context from event {event}')

    return {
        'statusCode': 200,
        'headers': {
            'content-type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Methods': '*',
        },
    }
