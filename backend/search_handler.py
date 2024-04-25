import json
import os

from dataall.base.db import get_engine
from dataall.base.searchproxy import connect, run_query
from dataall.base.config import config
from dataall.base.utils.api_handler_utils import send_unauthorized_response, get_custom_groups, get_cognito_groups
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyValidationService
from dataall.modules.maintenance.api.enums import MaintenanceModes, MaintenanceStatus
from dataall.modules.maintenance.services.maintenance_service import MaintenanceService

ENVNAME = os.getenv('envname', 'local')
ENGINE = get_engine(envname=ENVNAME)
es = connect(envname=ENVNAME)


def handler(event, context):
    print('Received event')
    print(event)
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
    elif event['httpMethod'] == 'POST':
        if 'authorizer' in event['requestContext']:
            if 'claims' not in event['requestContext']['authorizer']:
                claims = event['requestContext']['authorizer']
            else:
                claims = event['requestContext']['authorizer']['claims']

            # Needed for custom groups
            user_id = claims['email']
            if 'user_id' in event['requestContext']['authorizer']:
                user_id = event['requestContext']['authorizer']['user_id']

            groups = []
            if os.environ.get('custom_auth', None):
                groups.extend(get_custom_groups(user_id))
            else:
                groups.extend(get_cognito_groups(claims))

            # Check if maintenance window is enabled AND if the maintenance mode is NO-ACCESS
            if config.get_property('modules.maintenance.active'):
                if (
                    (MaintenanceService._get_maintenance_window_mode(engine=ENGINE) == MaintenanceModes.NOACCESS.value)
                    and (
                        MaintenanceService.get_maintenance_window_status(engine=ENGINE).status
                        is not MaintenanceStatus.INACTIVE.value
                    )
                    and not TenantPolicyValidationService.is_tenant_admin(groups)
                ):
                    send_unauthorized_response(
                        query={'operationName': 'OpensearchIndex'},
                        message='Access Restricted: data.all is currently undergoing maintenance, and your actions are temporarily blocked.',
                    )

            body = event.get('body')
            print(body)
            success = True
            try:
                response = run_query(es, 'dataall-index', body)
            except Exception:
                success = False
                response = {}
            return {
                'statusCode': 200 if success else 400,
                'headers': {
                    'content-type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Methods': '*',
                },
                'body': json.dumps(response),
            }
