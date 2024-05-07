import logging

from sqlalchemy.sql import and_

from dataall.base.db import paginate
from dataall.core.permissions.db.permission.permission_models import Permission
from dataall.core.permissions.db.tenant.tenant_models import TenantPolicy, Tenant, TenantPolicyPermission

logger = logging.getLogger(__name__)


class TenantPolicyRepository:
    ADMIN_GROUP = 'DAAdministrators'

    @staticmethod
    def has_user_tenant_permission(session, groups: [str], tenant_name: str, permission_name: str):
        tenant_policy: TenantPolicy = (
            session.query(TenantPolicy)
            .join(
                TenantPolicyPermission,
                TenantPolicy.sid == TenantPolicyPermission.sid,
            )
            .join(
                Tenant,
                Tenant.tenantUri == TenantPolicy.tenantUri,
            )
            .join(
                Permission,
                Permission.permissionUri == TenantPolicyPermission.permissionUri,
            )
            .filter(
                TenantPolicy.principalId.in_(groups),
                Permission.name == permission_name,
                Tenant.name == tenant_name,
            )
            .first()
        )
        return tenant_policy

    @staticmethod
    def has_group_tenant_permission(session, group_uri: str, tenant_name: str, permission_name: str):
        tenant_policy: TenantPolicy = (
            session.query(TenantPolicy)
            .join(
                TenantPolicyPermission,
                TenantPolicy.sid == TenantPolicyPermission.sid,
            )
            .join(
                Tenant,
                Tenant.tenantUri == TenantPolicy.tenantUri,
            )
            .join(
                Permission,
                Permission.permissionUri == TenantPolicyPermission.permissionUri,
            )
            .filter(
                and_(
                    TenantPolicy.principalId == group_uri,
                    Permission.name == permission_name,
                    Tenant.name == tenant_name,
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
            session.query(TenantPolicy)
            .join(Tenant, Tenant.tenantUri == TenantPolicy.tenantUri)
            .filter(
                and_(
                    TenantPolicy.principalId == group_uri,
                    Tenant.name == tenant_name,
                )
            )
            .first()
        )
        return tenant_policy

    @staticmethod
    def list_tenant_groups(session, data=None):
        query = session.query(
            TenantPolicy.principalId.label('name'),
            TenantPolicy.principalId.label('groupUri'),
        ).filter(
            and_(
                TenantPolicy.principalType == 'GROUP',
                TenantPolicy.principalId != TenantPolicyRepository.ADMIN_GROUP,
            )
        )

        if data and data.get('term'):
            query = query.filter(TenantPolicy.principalId.ilike('%' + data.get('term') + '%'))

        return paginate(
            query=query.order_by(TenantPolicy.principalId),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()
