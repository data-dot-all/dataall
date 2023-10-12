import logging
import os

from dataall.core.permissions.db.tenant_policy_repositories import TenantPolicy
from dataall.base.db import get_engine
# from dataall.base.loader import load_modules, ImportMode

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))
log = logging.getLogger(__name__)
# load_modules(modes={ImportMode.API})

ENVNAME = os.environ.get('envname', 'local')
TTL = int(os.environ.get('TTL', '5'))
ENGINE = get_engine(envname=ENVNAME)


def handler(event, context):
    print("EVENT", event)
    log.info('Lambda Event %s', event)
    log.debug('Env name %s', ENVNAME)
    log.debug('Engine %s', ENGINE.engine.url)
    try:
        data = {
            "email": event['request']['userAttributes']['email'],
            "clientId": event['callerContext']['clientId'],
            "userName": event['userName'],
            "userPoolId": event['userPoolId'],
            "ttl": TTL
        }
        print(data)
        with ENGINE.scoped_session() as session:
            reauth_session = TenantPolicy.update_reauth_session(session, data)
            print(reauth_session)
    except Exception as e:
        log.info(f'Error Updating ReAuth Session for User: {event.get("userName", "None")}')
        print(f'Error Updating ReAuth Session for User: {event.get("userName", "None")}')
    return event
