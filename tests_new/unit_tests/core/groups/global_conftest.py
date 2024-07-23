import pytest

from dataall.core.groups.db.group_models import Group
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.core.permissions.services.tenant_permissions import TENANT_ALL



def _create_group(db, tenant, name, user):
    with db.scoped_session() as session:
        group = Group(name=name, label=name, owner=user.username)
        session.add(group)
        session.commit()

        TenantPolicyService.attach_group_tenant_policy(
            session=session,
            group=name,
            permissions=TENANT_ALL,
            tenant_name=tenant.name,
        )
        return group


@pytest.fixture(scope='module')
def group1(db, tenant, user1):
    yield _create_group(db, tenant, 'testadmins', user1)


@pytest.fixture(scope='module')
def group2(db, tenant, user2):
    yield _create_group(db, tenant, 'dataengineers', user2)

