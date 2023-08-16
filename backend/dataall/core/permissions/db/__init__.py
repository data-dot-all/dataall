import logging

from dataall.core.permissions.db import permission_models
from dataall.core.permissions.db.permission_repositories import Permission
from dataall.core.permissions.db.tenant_repositories import Tenant

log = logging.getLogger("Permissions")


def save_permissions_with_tenant(engine, envname=None):
    with engine.scoped_session() as session:
        log.info('Initiating permissions')
        Tenant.save_tenant(session, name='dataall', description='Tenant dataall')
        Permission.init_permissions(session)
