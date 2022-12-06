import json
import logging
import os
from argparse import Namespace
from time import perf_counter

from ariadne import (
    gql,
    graphql_sync,
)

from common.api import bootstrap as bootstrap_schema, get_executable_schema
from common.db import init_permissions, get_engine, permissions, api, models
from common.search_proxy import connect


logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))
log = logging.getLogger(__name__)

start = perf_counter()
for name in ['boto3', 's3transfer', 'botocore', 'boto']:
    logging.getLogger(name).setLevel(logging.ERROR)

SCHEMA = bootstrap_schema()
TYPE_DEFS = gql(SCHEMA.gql(with_directives=False))
ENVNAME = os.getenv('envname', 'local')
ENGINE = get_engine(envname=ENVNAME)
ES = connect(envname=ENVNAME)

init_permissions(ENGINE)

executable_schema = get_executable_schema()
end = perf_counter()
print(f'Lambda Context ' f'Initialization took: {end - start:.3f} sec')

def resolver_adapter(resolver):
    def adapted(obj, info, **kwargs):
        return resolver(
            context=Namespace(
                engine=info.context['engine'],
                es=info.context['es'],
                username=info.context['username'],
                groups=info.context['groups'],
                schema=info.context['schema'],
                cdkproxyurl=info.context['cdkproxyurl'],
            ),
            source=obj or None,
            **kwargs,
        )

    return adapted


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
    log.debug('ElasticSearch %s', ES)
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
        username = event['requestContext']['authorizer']['claims']['email']
        try:
            groups = get_groups(event['requestContext']['authorizer']['claims'])
            with ENGINE.scoped_session() as session:
                for group in groups:
                    policy = api.TenantPolicy.find_tenant_policy(
                        session, group, 'dataall'
                    )
                    if not policy:
                        print(
                            f'No policy found for Team {group}. Attaching TENANT_ALL permissions'
                        )
                        api.TenantPolicy.attach_group_tenant_policy(
                            session=session,
                            group=group,
                            permissions=permissions.TENANT_ALL,
                            tenant_name='dataall',
                        )

        except Exception as e:
            print(f'Error managing groups due to: {e}')
            groups = []

        app_context = {
            'engine': ENGINE,
            'es': ES,
            'username': username,
            'groups': groups,
            'schema': SCHEMA,
            'cdkproxyurl': None,
        }
    else:
        raise Exception(f'Could not initialize user context from event {event}')

    query = json.loads(event.get('body'))
    success, response = graphql_sync(
        schema=executable_schema, data=query, context_value=app_context
    )
    response = json.dumps(response)

    log.info('Lambda Response %s', response)

    return {
        'statusCode': 200 if success else 400,
        'headers': {
            'content-type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Methods': '*',
        },
        'body': response,
    }