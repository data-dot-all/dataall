import datetime
import json
import os
import logging

from graphql import parse, utilities, OperationType, GraphQLSyntaxError
from dataall.base.aws.parameter_store import ParameterStoreManager
from dataall.base.db import get_engine
from dataall.base.services.service_provider_factory import ServiceProviderFactory
from dataall.core.permissions.services.tenant_permissions import TENANT_ALL
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.modules.maintenance.api.enums import MaintenanceModes, MaintenanceStatus
from dataall.modules.maintenance.services.maintenance_service import MaintenanceService
from dataall.base.config import config
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyValidationService

log = logging.getLogger(__name__)

ENVNAME = os.getenv('envname', 'local')
REAUTH_TTL = int(os.environ.get('REAUTH_TTL', '5'))
# ALLOWED OPERATIONS WHEN A USER IS NOT DATAALL ADMIN AND NO-ACCESS MODE IS SELECTED
MAINTENANCE_ALLOWED_OPERATIONS_WHEN_NO_ACCESS = [
    item.casefold() for item in ['getGroupsForUser', 'getMaintenanceWindowStatus']
]
ENGINE = get_engine(envname=ENVNAME)
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*')
AWS_REGION = os.getenv('AWS_REGION')


def redact_creds(event):
    if event.get('headers', {}).get('Authorization'):
        event['headers']['Authorization'] = 'XXXXXXXXXXXX'

    if event.get('multiValueHeaders', {}).get('Authorization'):
        event['multiValueHeaders']['Authorization'] = 'XXXXXXXXXXXX'
    return event


def get_cognito_groups(claims):
    if not claims:
        raise ValueError(
            'Received empty claims. Please verify authorizer configuration',
            claims,
        )
    groups = list()
    saml_groups = claims.get('custom:saml.groups', '')
    translation_table = str.maketrans({'[': '', ']': ''})
    if len(saml_groups):
        groups = saml_groups.translate(translation_table).replace(', ', ',').split(',')
    cognito_groups = claims.get('cognito:groups', '')
    if len(cognito_groups):
        groups.extend(cognito_groups.split(','))
    return groups


def get_custom_groups(user_id):
    service_provider = ServiceProviderFactory.get_service_provider_instance()
    return service_provider.get_groups_for_user(user_id)


def send_unauthorized_response(operation='', message='', extension=None):
    response = {
        'data': {operation: None},
        'errors': [
            {
                'message': message,
                'locations': None,
                'path': [operation],
            }
        ],
    }
    if extension is not None:
        response['errors'][0]['extensions'] = extension
    return {
        'statusCode': 401,
        'headers': {
            'content-type': 'application/json',
            'Access-Control-Allow-Origin': ALLOWED_ORIGINS,
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Methods': '*',
        },
        'body': json.dumps(response),
    }


def extract_groups(user_id, claims):
    groups = []
    try:
        if os.environ.get('custom_auth', None):
            groups.extend(get_custom_groups(user_id))
        else:
            groups.extend(get_cognito_groups(claims))
        log.debug('groups are %s', ','.join(groups))
        return groups
    except Exception as e:
        log.exception(f'Error managing groups due to: {e}')
        return groups


def attach_tenant_policy_for_groups(groups=None):
    if groups is None:
        groups = []
    with ENGINE.scoped_session() as session:
        for group in groups:
            policy = TenantPolicyService.find_tenant_policy(session, group, TenantPolicyService.TENANT_NAME)
            if not policy:
                log.info(f'No policy found for Team {group}. Attaching TENANT_ALL permissions')
                TenantPolicyService.attach_group_tenant_policy(
                    session=session,
                    group=group,
                    permissions=TENANT_ALL,
                    tenant_name=TenantPolicyService.TENANT_NAME,
                )


def check_reauth(query, auth_time, username):
    # Determine if there are any Operations that Require ReAuth From SSM Parameter
    try:
        reauth_apis = ParameterStoreManager.get_parameter_value(
            region=AWS_REGION, parameter_path=f'/dataall/{ENVNAME}/reauth/apis'
        ).split(',')
    except Exception:
        log.info('No ReAuth APIs Found in SSM')
        reauth_apis = None

    # If The Operation is a ReAuth Operation - Ensure A Non-Expired Session or Return Error
    if reauth_apis and query.get('operationName', None) in reauth_apis:
        now = datetime.datetime.now(datetime.timezone.utc)
        try:
            auth_time_datetime = datetime.datetime.fromtimestamp(int(auth_time), tz=datetime.timezone.utc)
            if auth_time_datetime + datetime.timedelta(minutes=REAUTH_TTL) < now:
                raise Exception('ReAuth')
        except Exception as e:
            log.info(f'ReAuth Required for User {username} on Operation {query.get("operationName", "")}, Error: {e}')
            return send_unauthorized_response(
                operation=query.get('operationName', 'operation'),
                message=f'ReAuth Required To Perform This Action {query.get("operationName", "")}',
                extension={'code': 'REAUTH'},
            )


def validate_and_block_if_maintenance_window(query, groups, blocked_for_mode_enum=None):
    """
    When the maintenance module is set to active, checks
        - If the maintenance mode is enabled
        - Based on the maintenance mode, actions which can be taken by user can be modified
            - READ-ONLY -> Block All Mutation calls and allow query graphql calls
            - NO-ACCESS -> Block All graphql query call irrespective of type
        - Check if the user belongs to the DAAdministrators group
    @param query: graphql query dict containing operation, query, variables
    @param groups: user groups
    @param blocked_for_mode_enum: sets the mode for blocking only specific modes. When set to None, both graphql types ( Query and Mutation ) will be blocked. When a specific mode is set, blocking will only occure for that mode
    @return: error response if maintenance window is blocking gql calls else None
    """
    if config.get_property('modules.maintenance.active'):
        maintenance_mode = MaintenanceService._get_maintenance_window_mode(engine=ENGINE)
        maintenance_status = MaintenanceService.get_maintenance_window_status().status
        isAdmin = TenantPolicyValidationService.is_tenant_admin(groups)

        if (
            (maintenance_mode == MaintenanceModes.NOACCESS.value)
            and (maintenance_status is not MaintenanceStatus.INACTIVE.value)
            and not isAdmin
            and (blocked_for_mode_enum is None or blocked_for_mode_enum == MaintenanceModes.NOACCESS)
        ):
            if query.get('operationName', '').casefold() not in MAINTENANCE_ALLOWED_OPERATIONS_WHEN_NO_ACCESS:
                return send_unauthorized_response(
                    operation=query.get('operationName', 'operation'),
                    message='Access Restricted: data.all is currently undergoing maintenance, and your actions are temporarily blocked.',
                )
        elif (
            (maintenance_mode == MaintenanceModes.READONLY.value)
            and (maintenance_status is not MaintenanceStatus.INACTIVE.value)
            and not isAdmin
            and (blocked_for_mode_enum is None or blocked_for_mode_enum == MaintenanceModes.READONLY)
        ):
            # If its mutation then block and return
            try:
                parsed_query_document = parse(query.get('query', ''))
                graphQL_operation_type = utilities.get_operation_ast(parsed_query_document)
                if graphQL_operation_type.operation == OperationType.MUTATION:
                    return send_unauthorized_response(
                        operation=query.get('operationName', 'operation'),
                        message='Access Restricted: data.all is currently undergoing maintenance, and your actions are temporarily blocked.',
                    )
            except GraphQLSyntaxError as e:
                log.error(
                    f'Error occured while parsing query when validating for {maintenance_mode} maintenance mode due to - {e}'
                )
                raise e
