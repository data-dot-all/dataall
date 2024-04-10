import pytest

from dataall.core.permissions.db.permission.permission_models import PermissionType
from dataall.core.permissions.services.permission_service import PermissionService
from dataall.base.db import exceptions
from dataall.core.permissions.services.environment_permissions import ENVIRONMENT_ALL
from dataall.core.permissions.services.organization_permissions import ORGANIZATION_ALL
from dataall.core.permissions.services.tenant_permissions import MANAGE_GROUPS, TENANT_ALL
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService


def permissions(db, all_perms):
    with db.scoped_session() as session:
        permissions = []
        for p in all_perms:
            permissions.append(
                PermissionService.save_permission(
                    session,
                    name=p,
                    description=p,
                    permission_type=PermissionType.RESOURCE.name,
                )
            )
        for p in TENANT_ALL:
            permissions.append(
                PermissionService.save_permission(
                    session,
                    name=p,
                    description=p,
                    permission_type=PermissionType.TENANT.name,
                )
            )
        session.commit()


def test_attach_tenant_policy(db, group, tenant):
    permissions(db, ORGANIZATION_ALL + ENVIRONMENT_ALL)
    with db.scoped_session() as session:
        TenantPolicyService.attach_group_tenant_policy(
            session=session,
            group=group.name,
            permissions=[MANAGE_GROUPS],
            tenant_name=TenantPolicyService.TENANT_NAME,
        )

        assert TenantPolicyService.check_user_tenant_permission(
            session=session,
            username='alice',
            groups=[group.name],
            permission_name=MANAGE_GROUPS,
            tenant_name=TenantPolicyService.TENANT_NAME,
        )


def test_unauthorized_tenant_policy(db, group):
    with pytest.raises(exceptions.TenantUnauthorized):
        with db.scoped_session() as session:
            assert TenantPolicyService.check_user_tenant_permission(
                session=session,
                username='alice',
                groups=[group.name],
                permission_name='UNKNOW_PERMISSION',
                tenant_name='dataall',
            )
