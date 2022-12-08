import logging

from sqlalchemy.sql import and_

from backend.db.paginator import paginate
from backend.db import models, exceptions, permissions
from backend.db.api.permission import Permission
from backend.db.api.tenant import Tenant

logger = logging.getLogger(__name__)

TENANT_NAME = 'dataall'


class TenantPolicy:
    @staticmethod
    def is_tenant_admin(groups: [str]):
        if not groups:
            return False

        if 'DAAdministrators' in groups:
            return True

        return False

    @staticmethod
    def check_user_tenant_permission(
        session, username: str, groups: [str], tenant_name: str, permission_name: str
    ):
        if TenantPolicy.is_tenant_admin(groups):
            return True

        tenant_policy = TenantPolicy.has_user_tenant_permission(
            session=session,
            username=username,
            groups=groups,
            permission_name=permission_name,
            tenant_name=tenant_name,
        )

        if not tenant_policy:
            raise exceptions.TenantUnauthorized(
                username=username,
                action=permission_name,
                tenant_name=tenant_name,
            )

        else:
            return tenant_policy

    @staticmethod
    def has_user_tenant_permission(
        session, username: str, groups: [str], tenant_name: str, permission_name: str
    ):
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
                models.Permission,
                models.Permission.permissionUri
                == models.TenantPolicyPermission.permissionUri,
            )
            .filter(
                models.TenantPolicy.principalId.in_(groups),
                models.Permission.name == permission_name,
                models.Tenant.name == tenant_name,
            )
            .first()
        )
        return tenant_policy

    @staticmethod
    def has_group_tenant_permission(
        session, group_uri: str, tenant_name: str, permission_name: str
    ):
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
                models.Permission,
                models.Permission.permissionUri
                == models.TenantPolicyPermission.permissionUri,
            )
            .filter(
                and_(
                    models.TenantPolicy.principalId == group_uri,
                    models.Permission.name == permission_name,
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

        TenantPolicy.validate_find_tenant_policy(group_uri, tenant_name)

        tenant_policy = (
            session.query(models.TenantPolicy)
            .join(
                models.Tenant, models.Tenant.tenantUri == models.TenantPolicy.tenantUri
            )
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
    def validate_find_tenant_policy(group_uri, tenant_name):
        if not group_uri:
            raise exceptions.RequiredParameter(param_name='group_uri')
        if not tenant_name:
            raise exceptions.RequiredParameter(param_name='tenant_name')

    @staticmethod
    def attach_group_tenant_policy(
        session,
        group: str,
        permissions: [str],
        tenant_name: str,
    ) -> models.TenantPolicy:

        TenantPolicy.validate_attach_tenant_policy(group, permissions, tenant_name)

        policy = TenantPolicy.save_group_tenant_policy(session, group, tenant_name)

        TenantPolicy.add_permission_to_group_tenant_policy(
            session, group, permissions, tenant_name, policy
        )

        return policy

    @staticmethod
    def validate_attach_tenant_policy(group, permissions, tenant_name):
        if not group:
            raise exceptions.RequiredParameter(param_name='group')
        if not permissions:
            raise exceptions.RequiredParameter(param_name='permissions')
        if not tenant_name:
            raise exceptions.RequiredParameter(param_name='tenant_name')

    @staticmethod
    def save_group_tenant_policy(session, group, tenant_name):

        TenantPolicy.validate_save_tenant_policy(group, tenant_name)

        policy = TenantPolicy.find_tenant_policy(session, group, tenant_name)
        if not policy:
            policy = models.TenantPolicy(
                principalId=group,
                principalType='GROUP',
                tenant=Tenant.get_tenant_by_name(session, tenant_name),
            )
            session.add(policy)
            session.commit()
        return policy

    @staticmethod
    def validate_save_tenant_policy(group, tenant_name):
        if not group:
            raise exceptions.RequiredParameter(param_name='group')
        if not tenant_name:
            raise exceptions.RequiredParameter(param_name='tenant_name')

    @staticmethod
    def add_permission_to_group_tenant_policy(
        session, group, permissions, tenant_name, policy
    ):
        TenantPolicy.validate_add_permission_to_tenant_policy_params(
            group, permissions, policy, tenant_name
        )

        for permission in permissions:
            if not TenantPolicy.has_group_tenant_permission(
                session,
                group_uri=group,
                permission_name=permission,
                tenant_name=tenant_name,
            ):
                TenantPolicy.associate_permission_to_tenant_policy(
                    session, policy, permission
                )

    @staticmethod
    def validate_add_permission_to_tenant_policy_params(
        group, permissions, policy, tenant_name
    ):
        if not group:
            raise exceptions.RequiredParameter(param_name='group')
        TenantPolicy.validate_add_permissions_params(permissions, policy, tenant_name)

    @staticmethod
    def validate_add_permissions_params(permissions, policy, tenant_name):
        if not permissions:
            raise exceptions.RequiredParameter(param_name='permissions')
        if not tenant_name:
            raise exceptions.RequiredParameter(param_name='tenant_name')
        if not policy:
            raise exceptions.RequiredParameter(param_name='policy')

    @staticmethod
    def associate_permission_to_tenant_policy(session, policy, permission):
        policy_permission = models.TenantPolicyPermission(
            sid=policy.sid,
            permissionUri=Permission.get_permission_by_name(
                session, permission, models.PermissionType.TENANT.name
            ).permissionUri,
        )
        session.add(policy_permission)
        session.commit()

    @staticmethod
    def get_tenant_policy_permissions(session, group_uri, tenant_name):
        if not group_uri:
            raise exceptions.RequiredParameter(param_name='group_uri')
        if not tenant_name:
            raise exceptions.RequiredParameter(param_name='tenant_name')
        policy = TenantPolicy.find_tenant_policy(
            session=session,
            group_uri=group_uri,
            tenant_name=tenant_name,
        )
        permissions = []
        for p in policy.permissions:
            permissions.append(p.permission)
        return permissions

    @staticmethod
    def delete_tenant_policy(
        session,
        group: str,
        tenant_name: str,
    ) -> bool:

        policy = TenantPolicy.find_tenant_policy(
            session, group_uri=group, tenant_name=tenant_name
        )
        if policy:
            for permission in policy.permissions:
                session.delete(permission)
            session.delete(policy)
            session.commit()

        return True

    @staticmethod
    def list_group_tenant_permissions(
        session, username, groups, uri, data=None, check_perm=None
    ):
        if not groups:
            raise exceptions.RequiredParameter('groups')
        if not uri:
            raise exceptions.RequiredParameter('groupUri')

        if not TenantPolicy.is_tenant_admin(groups):
            raise exceptions.UnauthorizedOperation(
                action='LIST_TENANT_TEAM_PERMISSIONS',
                message=f'User: {username} is not allowed to manage tenant permissions',
            )

        return TenantPolicy.get_tenant_policy_permissions(
            session=session,
            group_uri=uri,
            tenant_name='dataall',
        )

    @staticmethod
    def list_tenant_groups(session, username, groups, uri, data=None, check_perm=None):
        if not groups:
            raise exceptions.RequiredParameter('groups')

        if not TenantPolicy.is_tenant_admin(groups):
            raise exceptions.UnauthorizedOperation(
                action='LIST_TENANT_TEAMS',
                message=f'User: {username} is not allowed to manage tenant permissions',
            )

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
            query = query.filter(
                models.TenantPolicy.principalId.ilike('%' + data.get('term') + '%')
            )

        return paginate(
            query=query,
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    def list_tenant_permissions(session, username, groups):
        if not TenantPolicy.is_tenant_admin(groups):
            raise exceptions.UnauthorizedOperation(
                action='LIST_TENANT_TEAM_PERMISSIONS',
                message=f'User: {username} is not allowed to manage tenant permissions',
            )
        group_invitation_permissions = []
        for p in permissions.TENANT_ALL:
            group_invitation_permissions.append(
                Permission.find_permission_by_name(
                    session=session,
                    permission_name=p,
                    permission_type=models.PermissionType.TENANT.name,
                )
            )
        return group_invitation_permissions

    @staticmethod
    def update_group_permissions(
        session, username, groups, uri, data=None, check_perm=None
    ):
        TenantPolicy.validate_params(data)

        if not TenantPolicy.is_tenant_admin(groups):
            exceptions.UnauthorizedOperation(
                action='UPDATE_TENANT_TEAM_PERMISSIONS',
                message=f'User: {username} is not allowed to manage tenant permissions',
            )

        TenantPolicy.validate_permissions(
            session, TENANT_NAME, data['permissions'], uri
        )

        TenantPolicy.delete_tenant_policy(
            session=session, group=uri, tenant_name=TENANT_NAME
        )
        TenantPolicy.attach_group_tenant_policy(
            session=session,
            group=uri,
            permissions=data['permissions'],
            tenant_name=TENANT_NAME,
        )

        return True

    @staticmethod
    def validate_permissions(session, tenant_name, g_permissions, group):
        g_permissions = list(set(g_permissions))

        if g_permissions not in permissions.TENANT_ALL:
            exceptions.TenantPermissionUnauthorized(
                action='UPDATE_TENANT_TEAM_PERMISSIONS',
                group_name=group,
                tenant_name=tenant_name,
            )

        tenant_group_permissions = []
        for p in g_permissions:
            tenant_group_permissions.append(
                Permission.find_permission_by_name(
                    session=session,
                    permission_name=p,
                    permission_type=models.PermissionType.TENANT.name,
                )
            )
        return tenant_group_permissions

    @staticmethod
    def validate_params(data):
        if not data:
            raise exceptions.RequiredParameter('data')
        if not data.get('permissions'):
            raise exceptions.RequiredParameter('permissions')
