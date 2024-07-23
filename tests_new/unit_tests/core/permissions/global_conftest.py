import pytest

from dataall.core.permissions.services.permission_service import PermissionService
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService

@pytest.fixture(scope='module', autouse=True)
def tenant(db, permissions):
    with db.scoped_session() as session:
        tenant = TenantPolicyService.save_tenant(session, name='dataall', description='Tenant dataall')
        yield tenant

@pytest.fixture(scope='module', autouse=True)
def permissions(db):
    with db.scoped_session() as session:
        yield PermissionService.init_permissions(session)
