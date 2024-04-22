"""
The handler of this module will be called once upon every deployment
"""

import logging
import os

from dataall.base.db import get_engine
from dataall.base.loader import load_modules, ImportMode
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))


def handler(event, context) -> None:
    load_modules(modes={ImportMode.API})
    envname = os.getenv('envname', 'local')
    engine = get_engine(envname=envname)
    TenantPolicyService.save_permissions_with_tenant(engine)
