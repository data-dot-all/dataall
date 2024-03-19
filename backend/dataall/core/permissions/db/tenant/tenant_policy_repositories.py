import logging

from sqlalchemy.sql import and_

from dataall.core.permissions.api.enums import PermissionType
from dataall.base.db import exceptions, paginate
from dataall.core.permissions.constants import permissions
from dataall.core.permissions.db.permission import permission_models
from dataall.core.permissions.db.tenant import tenant_models as models
from dataall.core.permissions.db.permission.permission_repositories import Permission

logger = logging.getLogger(__name__)


class TenantPolicy:
    TENANT_NAME = 'dataall'

    @staticmethod
    def has_user_tenant_permission(session, username: str, groups: [str], tenant_name: str, permission_name: str):
        if not username or not permission_name:
            return False
        tenant_policy: models.TenantPolicy = (
            session.query(models.TenantPolicy)
            .join(
                models.TenantPolicyPermission,
                models.TenantPolicy.sid == models.TenantPolicyPermission.sid,
            )
            .join(
                models.Tenant,
                models.Tenant.tenantUri == models.TenantPolicy.tenantUri,
            )
            .join(
                permission_models.Permission,
                permission_models.Permission.permissionUri == models.TenantPolicyPermission.permissionUri,
            )
            .filter(
                models.TenantPolicy.principalId.in_(groups),
                permission_models.Permission.name == permission_name,
                models.Tenant.name == tenant_name,
            )
            .first()
        )
        return tenant_policy

    @staticmethod
    def has_group_tenant_permission(session, group_uri: str, tenant_name: str, permission_name: str):
        if not group_uri or not permission_name:
            return False

        tenant_policy: models.TenantPolicy = (
            session.query(models.TenantPolicy)
            .join(
                models.TenantPolicyPermission,
                models.TenantPolicy.sid == models.TenantPolicyPermission.sid,
            )
            .join(
                models.Tenant,
                models.Tenant.tenantUri == models.TenantPolicy.tenantUri,
            )
            .join(
                permission_models.Permission,
                permission_models.Permission.permissionUri == models.TenantPolicyPermission.permissionUri,
            )
            .filter(
                and_(
                    models.TenantPolicy.principalId == group_uri,
                    permission_models.Permission.name == permission_name,
                    models.Tenant.name == tenant_name,
                )
            )
            .first()
        )

        if not tenant_policy:
            return False
        else:
            return tenant_policy

    @staticmethod
    def find_tenant_policy(session, group_uri: str, tenant_name: str):
        tenant_policy = (
            session.query(models.TenantPolicy)
            .join(models.Tenant, models.Tenant.tenantUri == models.TenantPolicy.tenantUri)
            .filter(
                and_(
                    models.TenantPolicy.principalId == group_uri,
                    models.Tenant.name == tenant_name,
                )
            )
            .first()
        )
        return tenant_policy

    @staticmethod
    def list_tenant_groups(session, data=None):
        query = session.query(
            models.TenantPolicy.principalId.label('name'),
            models.TenantPolicy.principalId.label('groupUri'),
        ).filter(
            and_(
                models.TenantPolicy.principalType == 'GROUP',
                models.TenantPolicy.principalId != 'DAAdministrators',
            )
        )

        if data and data.get('term'):
            query = query.filter(models.TenantPolicy.principalId.ilike('%' + data.get('term') + '%'))

        return paginate(
            query=query,
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()
