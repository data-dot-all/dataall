import pytest

from dataall.core.permissions.db.permission_repositories import Permission
from dataall.core.permissions.db.permission_models import PermissionType
from dataall.core.permissions.db.tenant_policy_repositories import TenantPolicy
from dataall.base.db import exceptions
from dataall.core.permissions.permissions import MANAGE_GROUPS, ENVIRONMENT_ALL, ORGANIZATION_ALL, TENANT_ALL


def permissions(db, all_perms):
    with db.scoped_session() as session:
        permissions = []
        for p in all_perms:
            permissions.append(
                Permission.save_permission(
                    session,
                    name=p,
                    description=p,
                    permission_type=PermissionType.RESOURCE.name,
                )
            )
        for p in TENANT_ALL:
            permissions.append(
                Permission.save_permission(
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
        TenantPolicy.attach_group_tenant_policy(
            session=session,
            group=group.name,
            permissions=[MANAGE_GROUPS],
            tenant_name='dataall',
        )

        assert TenantPolicy.check_user_tenant_permission(
            session=session,
            username='alice',
            groups=[group.name],
            permission_name=MANAGE_GROUPS,
            tenant_name='dataall',
        )


def test_unauthorized_tenant_policy(db, group):
    with pytest.raises(exceptions.TenantUnauthorized):
        with db.scoped_session() as session:
            assert TenantPolicy.check_user_tenant_permission(
                session=session,
                username='alice',
                groups=[group.name],
                permission_name='UNKNOW_PERMISSION',
                tenant_name='dataall',
            )
