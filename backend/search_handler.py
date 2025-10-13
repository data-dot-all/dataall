import json
import os
import logging

from dataall.base.context import RequestContext, set_context
from dataall.base.db import get_engine
from dataall.base.searchproxy import connect, run_query
from dataall.base.utils.api_handler_utils import validate_and_block_if_maintenance_window, extract_groups, redact_creds
from dataall.modules.maintenance.api.enums import MaintenanceModes


logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))
log = logging.getLogger(__name__)

ENVNAME = os.getenv('envname', 'local')
es = connect(envname=ENVNAME)
ENGINE = get_engine(envname=ENVNAME)
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*')


def handler(event, context):
    event = redact_creds(event)
    logger.info('Received event')
    logger.info(event)
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
    elif event['httpMethod'] == 'POST':
        if 'authorizer' in event['requestContext']:
            if 'claims' not in event['requestContext']['authorizer']:
                claims = event['requestContext']['authorizer']
            else:
                claims = event['requestContext']['authorizer']['claims']

            username = claims['email']

            # Needed for custom groups
            user_id = claims['email']
            if 'user_id' in event['requestContext']['authorizer']:
                user_id = event['requestContext']['authorizer']['user_id']

            groups: list = extract_groups(user_id, claims)

            set_context(RequestContext(ENGINE, username, groups, user_id))

            # Check if maintenance window is enabled AND if the maintenance mode is NO-ACCESS
            maintenance_window_validation_response = validate_and_block_if_maintenance_window(
                query={'operationName': 'OpensearchIndex'},
                groups=groups,
                blocked_for_mode_enum=MaintenanceModes.NOACCESS,
            )
            if maintenance_window_validation_response is not None:
                return maintenance_window_validation_response

            body = event.get('body')
            logger.info(body)
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
                    'Access-Control-Allow-Origin': ALLOWED_ORIGINS,
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Methods': '*',
                },
                'body': json.dumps(response),
            }
