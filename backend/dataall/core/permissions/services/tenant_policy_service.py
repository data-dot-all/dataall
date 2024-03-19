from dataall.core.permissions.db.tenant.tenant_policy_repositories import TenantPolicy
from dataall.core.permissions.constants import permissions
from dataall.core.permissions.db.permission.permission_repositories import Permission
from dataall.core.permissions.api.enums import PermissionType
from dataall.base.db import exceptions
from dataall.core.permissions.db.tenant.tenant_models import TenantPolicy as TenantPolicyModel, TenantPolicyPermission
from dataall.core.permissions.db.tenant.tenant_repositories import Tenant as TenantService


class TenantPolicyValidationService:
    @staticmethod
    def is_tenant_admin(groups: [str]):
        if not groups:
            return False

        if 'DAAdministrators' in groups:
            return True

        return False

    @staticmethod
    def validate_admin_access(username, groups, action):
        if not TenantPolicyValidationService.is_tenant_admin(groups):
            raise exceptions.UnauthorizedOperation(
                action=action,
                message=f'User: {username} is not allowed to manage tenant permissions',
            )

    @staticmethod
    def validate_find_tenant_policy(group_uri, tenant_name):
        if not group_uri:
            raise exceptions.RequiredParameter(param_name='group_uri')
        if not tenant_name:
            raise exceptions.RequiredParameter(param_name='tenant_name')

    @staticmethod
    def validate_attach_tenant_policy(group, permissions, tenant_name):
        if not group:
            raise exceptions.RequiredParameter(param_name='group')
        if not permissions:
            raise exceptions.RequiredParameter(param_name='permissions')
        if not tenant_name:
            raise exceptions.RequiredParameter(param_name='tenant_name')

    @staticmethod
    def validate_save_tenant_policy(group, tenant_name):
        if not group:
            raise exceptions.RequiredParameter(param_name='group')
        if not tenant_name:
            raise exceptions.RequiredParameter(param_name='tenant_name')

    @staticmethod
    def validate_add_permission_to_tenant_policy_params(group, permissions, policy, tenant_name):
        if not group:
            raise exceptions.RequiredParameter(param_name='group')
        TenantPolicyValidationService.validate_add_permissions_params(permissions, policy, tenant_name)

    @staticmethod
    def validate_add_permissions_params(permissions, policy, tenant_name):
        if not permissions:
            raise exceptions.RequiredParameter(param_name='permissions')
        if not tenant_name:
            raise exceptions.RequiredParameter(param_name='tenant_name')
        if not policy:
            raise exceptions.RequiredParameter(param_name='policy')

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
                    permission_type=PermissionType.TENANT.name,
                )
            )
        return tenant_group_permissions

    @staticmethod
    def validate_params(data):
        if not data:
            raise exceptions.RequiredParameter('data')
        if not data.get('permissions'):
            raise exceptions.RequiredParameter('permissions')


class TenantPolicyService:
    @staticmethod
    def update_group_permissions(session, username, groups, uri, data=None, check_perm=None):
        TenantPolicyValidationService.validate_params(data)
        new_permissions = data['permissions']

        # raises UnauthorizedOperation exception, if there is no admin access
        TenantPolicyValidationService.validate_admin_access(username, groups, 'UPDATE_TENANT_TEAM_PERMISSIONS')

        TenantPolicyValidationService.validate_permissions(session, TenantPolicy.TENANT_NAME, new_permissions, uri)

        TenantPolicyService.delete_tenant_policy(session=session, group=uri, tenant_name=TenantPolicy.TENANT_NAME)
        TenantPolicyService.attach_group_tenant_policy(
            session=session,
            group=uri,
            permissions=new_permissions,
            tenant_name=TenantPolicy.TENANT_NAME,
        )

        return True

    @staticmethod
    def list_tenant_permissions(session, username, groups):
        TenantPolicyValidationService.validate_admin_access(username, groups, 'LIST_TENANT_TEAM_PERMISSIONS')

        group_invitation_permissions = []
        for p in permissions.TENANT_ALL:
            group_invitation_permissions.append(
                Permission.find_permission_by_name(
                    session=session,
                    permission_name=p,
                    permission_type=PermissionType.TENANT.name,
                )
            )
        return group_invitation_permissions

    @staticmethod
    def list_tenant_groups(session, username, groups, data=None):
        if not groups:
            raise exceptions.RequiredParameter('groups')

        TenantPolicyValidationService.validate_admin_access(username, groups, 'LIST_TENANT_TEAMS')

        return TenantPolicy.list_tenant_groups(session, data)

    @staticmethod
    def check_user_tenant_permission(session, username: str, groups: [str], tenant_name: str, permission_name: str):
        if TenantPolicyValidationService.is_tenant_admin(groups):
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
    def attach_group_tenant_policy(
        session,
        group: str,
        permissions: [str],
        tenant_name: str,
    ) -> TenantPolicyModel:
        TenantPolicyValidationService.validate_attach_tenant_policy(group, permissions, tenant_name)

        policy = TenantPolicyService.save_group_tenant_policy(session, group, tenant_name)

        TenantPolicyService.add_permission_to_group_tenant_policy(session, group, permissions, tenant_name, policy)

        return policy

    @staticmethod
    def find_tenant_policy(session, group_uri: str, tenant_name: str):
        TenantPolicyValidationService.validate_find_tenant_policy(group_uri, tenant_name)
        return TenantPolicy.find_tenant_policy(session, group_uri, tenant_name)

    @staticmethod
    def save_group_tenant_policy(session, group, tenant_name):
        TenantPolicyValidationService.validate_save_tenant_policy(group, tenant_name)

        policy = TenantPolicy.find_tenant_policy(session, group, tenant_name)
        if not policy:
            policy = TenantPolicyModel(
                principalId=group,
                principalType='GROUP',
                tenant=TenantService.get_tenant_by_name(session, tenant_name),
            )
            session.add(policy)
            session.commit()
        return policy

    @staticmethod
    def add_permission_to_group_tenant_policy(session, group, permissions, tenant_name, policy):
        TenantPolicyValidationService.validate_add_permission_to_tenant_policy_params(
            group, permissions, policy, tenant_name
        )

        for permission in permissions:
            if not TenantPolicy.has_group_tenant_permission(
                session,
                group_uri=group,
                permission_name=permission,
                tenant_name=tenant_name,
            ):
                TenantPolicyService.associate_permission_to_tenant_policy(session, policy, permission)

    @staticmethod
    def associate_permission_to_tenant_policy(session, policy, permission):
        policy_permission = TenantPolicyPermission(
            sid=policy.sid,
            permissionUri=Permission.get_permission_by_name(
                session, permission, PermissionType.TENANT.name
            ).permissionUri,
        )
        session.add(policy_permission)
        session.commit()

    @staticmethod
    def list_group_tenant_permissions(session, username, groups, uri, data=None, check_perm=None):
        if not groups:
            raise exceptions.RequiredParameter('groups')
        if not uri:
            raise exceptions.RequiredParameter('groupUri')

        TenantPolicyValidationService.validate_admin_access(username, groups, 'LIST_TENANT_TEAM_PERMISSIONS')

        return TenantPolicyService.get_tenant_policy_permissions(
            session=session,
            group_uri=uri,
            tenant_name='dataall',
        )

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
        policy = TenantPolicy.find_tenant_policy(session, group_uri=group, tenant_name=tenant_name)
        if policy:
            for permission in policy.permissions:
                session.delete(permission)
            session.delete(policy)
            session.commit()

        return True
