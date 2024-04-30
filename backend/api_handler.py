import json
import logging
import os
import datetime
from argparse import Namespace
from time import perf_counter

from ariadne import (
    gql,
    graphql_sync,
)

from dataall.base.api import bootstrap as bootstrap_schema, get_executable_schema
from dataall.base.services.service_provider_factory import ServiceProviderFactory
from dataall.base.utils.api_handler_utils import get_custom_groups, get_cognito_groups, send_unauthorized_response
from dataall.core.tasks.service_handlers import Worker
from dataall.base.aws.sqs import SqsQueue
from dataall.base.aws.parameter_store import ParameterStoreManager
from dataall.base.context import set_context, dispose_context, RequestContext
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService, TenantPolicyValidationService
from dataall.base.db import get_engine
from dataall.core.permissions.services.tenant_permissions import TENANT_ALL
from dataall.base.loader import load_modules, ImportMode
from dataall.modules.maintenance.api.enums import MaintenanceModes, MaintenanceStatus
from dataall.modules.maintenance.services.maintenance_service import MaintenanceService
from dataall.base.config import config

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))
log = logging.getLogger(__name__)

start = perf_counter()
for name in ['boto3', 's3transfer', 'botocore', 'boto']:
    logging.getLogger(name).setLevel(logging.ERROR)

load_modules(modes={ImportMode.API})
SCHEMA = bootstrap_schema()
TYPE_DEFS = gql(SCHEMA.gql(with_directives=False))
REAUTH_TTL = int(os.environ.get('REAUTH_TTL', '5'))
ENVNAME = os.getenv('envname', 'local')
ENGINE = get_engine(envname=ENVNAME)
Worker.queue = SqsQueue.send

TenantPolicyService.save_permissions_with_tenant(ENGINE)

MAINTENANCE_ALLOWED_OPERATIONS = ["getGroupsForUser", "getMaintenanceWindowStatus"]


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
        # Defaulting user_id field to contain email
        # When "authorizer" in the event contains the user_id field override with that value
        # user_id is used when deploying data.all with custom_auth
        user_id = claims['email']
        if 'user_id' in event['requestContext']['authorizer']:
            user_id = event['requestContext']['authorizer']['user_id']
        log.debug('username is %s', username)
        try:
            groups = []
            if os.environ.get('custom_auth', None):
                groups.extend(get_custom_groups(user_id))
            else:
                groups.extend(get_cognito_groups(claims))
            log.debug('groups are %s', ','.join(groups))
            with ENGINE.scoped_session() as session:
                for group in groups:
                    policy = TenantPolicyService.find_tenant_policy(session, group, TenantPolicyService.TENANT_NAME)
                    if not policy:
                        print(f'No policy found for Team {group}. Attaching TENANT_ALL permissions')
                        TenantPolicyService.attach_group_tenant_policy(
                            session=session,
                            group=group,
                            permissions=TENANT_ALL,
                            tenant_name=TenantPolicyService.TENANT_NAME,
                        )

        except Exception as e:
            print(f'Error managing groups due to: {e}')
            groups = []

        set_context(RequestContext(ENGINE, username, groups, user_id))

        app_context = {
            'engine': ENGINE,
            'username': username,
            'groups': groups,
            'schema': SCHEMA,
        }

        query = json.loads(event.get('body'))

        # Logic to block when in maintenance
        # Check if in some maintenance mode
        # Check if in maintenance status is not INACTIVE
        # Check if the user belongs to a 'DAAdministrators' group
        # Todo : Add check to see if maintenance module is enabled or not from the config
        if config.get_property('modules.maintenance.active'):
            if (
                (MaintenanceService._get_maintenance_window_mode(engine=ENGINE) == MaintenanceModes.NOACCESS.value)
                and (
                    MaintenanceService.get_maintenance_window_status(engine=ENGINE).status
                    is not MaintenanceStatus.INACTIVE.value
                )
                and not TenantPolicyValidationService.is_tenant_admin(groups)
            ):
                if query.get('operationName', '') not in MAINTENANCE_ALLOWED_OPERATIONS:
                    return send_unauthorized_response(
                        query=query,
                        message='Access Restricted: data.all is currently undergoing maintenance, and your actions are temporarily blocked.',
                    )
            elif (
                (MaintenanceService._get_maintenance_window_mode(engine=ENGINE) == MaintenanceModes.READONLY.value)
                and (
                    MaintenanceService.get_maintenance_window_status(engine=ENGINE).status
                    is not MaintenanceStatus.INACTIVE.value
                )
                and not TenantPolicyValidationService.is_tenant_admin(groups)
            ):
                # If its mutation then block and return
                if query.get('query', '').split()[0] == 'mutation':
                    return send_unauthorized_response(
                        query=query,
                        message='Access Restricted: data.all is currently undergoing maintenance, and your actions are temporarily blocked.',
                    )

        # Determine if there are any Operations that Require ReAuth From SSM Parameter
        try:
            reauth_apis = ParameterStoreManager.get_parameter_value(
                region=os.getenv('AWS_REGION', 'eu-west-1'), parameter_path=f'/dataall/{ENVNAME}/reauth/apis'
            ).split(',')
        except Exception:
            log.info('No ReAuth APIs Found in SSM')
            reauth_apis = None
    else:
        raise Exception(f'Could not initialize user context from event {event}')

    # If The Operation is a ReAuth Operation - Ensure A Non-Expired Session or Return Error
    if reauth_apis and query.get('operationName', None) in reauth_apis:
        now = datetime.datetime.now(datetime.timezone.utc)
        try:
            auth_time_datetime = datetime.datetime.fromtimestamp(int(claims['auth_time']), tz=datetime.timezone.utc)
            if auth_time_datetime + datetime.timedelta(minutes=REAUTH_TTL) < now:
                raise Exception('ReAuth')
        except Exception as e:
            log.info(f'ReAuth Required for User {username} on Operation {query.get("operationName", "")}, Error: {e}')
            response = {
                'data': {query.get('operationName', 'operation'): None},
                'errors': [
                    {
                        'message': f"ReAuth Required To Perform This Action {query.get('operationName', '')}",
                        'locations': None,
                        'path': [query.get('operationName', '')],
                        'extensions': {'code': 'REAUTH'},
                    }
                ],
            }
            return {
                'statusCode': 401,
                'headers': {
                    'content-type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Methods': '*',
                },
                'body': json.dumps(response),
            }

    success, response = graphql_sync(schema=executable_schema, data=query, context_value=app_context)

    dispose_context()
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
