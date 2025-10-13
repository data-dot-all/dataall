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
from dataall.base.utils.api_handler_utils import (
    extract_groups,
    attach_tenant_policy_for_groups,
    check_reauth,
    validate_and_block_if_maintenance_window,
    redact_creds,
)
from dataall.core.tasks.service_handlers import Worker
from dataall.base.aws.sqs import SqsQueue
from dataall.base.context import set_context, dispose_context, RequestContext
from dataall.base.db import get_engine
from dataall.base.loader import load_modules, ImportMode

from graphql.pyutils import did_you_mean

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))
log = logging.getLogger(__name__)

start = perf_counter()
for name in ['boto3', 's3transfer', 'botocore', 'boto']:
    logging.getLogger(name).setLevel(logging.ERROR)

ALLOW_INTROSPECTION = True if os.getenv('ALLOW_INTROSPECTION') == 'True' else False

if not ALLOW_INTROSPECTION:
    did_you_mean.__globals__['MAX_LENGTH'] = 0

load_modules(modes={ImportMode.API})
SCHEMA = bootstrap_schema()
TYPE_DEFS = gql(SCHEMA.gql(with_directives=False))
ENVNAME = os.getenv('envname', 'local')
ENGINE = get_engine(envname=ENVNAME)
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*')
Worker.queue = SqsQueue.send


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
print(f'Lambda Context Initialization took: {end - start:.3f} sec')


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

    event = redact_creds(event)
    log.info('Lambda Event %s', event)
    log.debug('Env name %s', ENVNAME)
    log.debug('Engine %s', ENGINE.engine.url)

    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'content-type': 'application/json',
                'Access-Control-Allow-Origin': ALLOWED_ORIGINS,
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
        # Defaulting user_id field to contain email
        # When "authorizer" in the event contains the user_id field override with that value
        # user_id is used when deploying data.all with custom_auth
        user_id = claims['email']
        if 'user_id' in event['requestContext']['authorizer']:
            user_id = event['requestContext']['authorizer']['user_id']
        log.debug('username is %s', username)

        groups: list = extract_groups(user_id=user_id, claims=claims)
        attach_tenant_policy_for_groups(groups=groups)

        set_context(RequestContext(ENGINE, username, groups, user_id))
        app_context = {
            'engine': ENGINE,
            'username': username,
            'groups': groups,
            'schema': SCHEMA,
        }

        query = json.loads(event.get('body'))

        maintenance_window_validation_response = validate_and_block_if_maintenance_window(query=query, groups=groups)
        if maintenance_window_validation_response is not None:
            return maintenance_window_validation_response
        reauth_validation_response = check_reauth(query=query, auth_time=claims['auth_time'], username=username)
        if reauth_validation_response is not None:
            return reauth_validation_response

    else:
        raise Exception(f'Could not initialize user context from event {event}')

    success, response = graphql_sync(
        schema=executable_schema, data=query, context_value=app_context, introspection=ALLOW_INTROSPECTION
    )

    dispose_context()
    response = json.dumps(response)

    log.info('Lambda Response Success: %s', success)
    log.debug('Lambda Response %s', response)
    return {
        'statusCode': 200 if success else 400,
        'headers': {
            'content-type': 'application/json',
            'Access-Control-Allow-Origin': ALLOWED_ORIGINS,
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Methods': '*',
        },
        'body': response,
    }
