from dataall.core.permissions.db.tenant.tenant_policy_repositories import TenantPolicyRepository
from dataall.core.permissions.services.tenant_permissions import TENANT_ALL
from dataall.core.permissions.db.permission.permission_repositories import PermissionRepository
from dataall.core.permissions.api.enums import PermissionType
from dataall.base.db import exceptions
from dataall.core.permissions.db.tenant.tenant_models import TenantPolicy, TenantPolicyPermission
from dataall.base.context import get_context
from dataall.core.permissions.db.tenant.tenant_repositories import TenantRepository
from dataall.core.permissions.services.permission_service import PermissionService
from dataall.core.permissions.db.tenant.tenant_models import Tenant
from dataall.base.services.service_provider_factory import ServiceProviderFactory
from dataall.base.aws.sts import SessionHelper
from dataall.base.aws.parameter_store import ParameterStoreManager
import logging
import os
from functools import wraps


log = logging.getLogger('Permissions')

ENVNAME = os.getenv('envname', 'local')
REGION = os.getenv('AWS_REGION', 'eu-west-1')


class RequestValidationService:
    @staticmethod
    def validate_groups_param(groups):
        if not groups:
            raise exceptions.RequiredParameter('groups')

    @staticmethod
    def validate_group_uri_param(groups, uri):
        RequestValidationService.validate_groups_param(groups)
        if not uri:
            raise exceptions.RequiredParameter('groupUri')

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
        if not permissions:
            raise exceptions.RequiredParameter(param_name='permissions')
        if not tenant_name:
            raise exceptions.RequiredParameter(param_name='tenant_name')
        if not policy:
            raise exceptions.RequiredParameter(param_name='policy')

    @staticmethod
    def validate_update_group_permission_params(data):
        if not data:
            raise exceptions.RequiredParameter('data')
        if not data.get('permissions'):
            raise exceptions.RequiredParameter('permissions')
        if not data.get('groupUri'):
            raise exceptions.RequiredParameter('groupUri')
        groups = ServiceProviderFactory.get_service_provider_instance().list_groups(envname=ENVNAME, region=REGION)
        if data.get('groupUri') not in groups:
            raise exceptions.InvalidInput('groupUri', data.get('groupUri'), ' a valid group')


class TenantPolicyValidationService:
    @staticmethod
    def is_tenant_admin(groups: [str]):
        if not groups:
            return False

        if TenantPolicyRepository.ADMIN_GROUP in groups:
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
    def validate_permissions(session, tenant_name, g_permissions, group):
        g_permissions = list(set(g_permissions))

        if g_permissions not in TENANT_ALL:
            exceptions.TenantPermissionUnauthorized(
                action='UPDATE_TENANT_TEAM_PERMISSIONS',
                group_name=group,
                tenant_name=tenant_name,
            )

        tenant_group_permissions = []
        for p in g_permissions:
            tenant_group_permissions.append(
                PermissionRepository.find_permission_by_name(
                    session=session,
                    permission_name=p,
                    permission_type=PermissionType.TENANT.name,
                )
            )
        return tenant_group_permissions


class TenantActionsService:
    @staticmethod
    def update_monitoring_ssm_parameter(name, value):
        # raises UnauthorizedOperation exception, if there is no admin access
        context = get_context()
        TenantPolicyValidationService.validate_admin_access(
            context.username, context.groups, 'UPDATE_SSM_PARAMETER_MONITORING'
        )

        current_account = SessionHelper.get_account()
        region = os.getenv('AWS_REGION', 'eu-west-1')
        response = ParameterStoreManager.update_parameter(
            AwsAccountId=current_account,
            region=region,
            parameter_name=f'/dataall/{os.getenv("envname", "local")}/quicksightmonitoring/{name}',
            parameter_value=value,
        )
        return response


class TenantPolicyService:
    TENANT_NAME = 'dataall'

    @staticmethod
    def update_group_permissions(data, check_perm=None):
        RequestValidationService.validate_update_group_permission_params(data)

        context = get_context()
        username = context.username
        groups = context.groups

        uri = data.get('groupUri')

        new_permissions = data['permissions']

        # raises UnauthorizedOperation exception, if there is no admin access
        TenantPolicyValidationService.validate_admin_access(username, groups, 'UPDATE_TENANT_TEAM_PERMISSIONS')

        with context.db_engine.scoped_session() as session:
            TenantPolicyValidationService.validate_permissions(
                session, TenantPolicyService.TENANT_NAME, new_permissions, uri
            )

            TenantPolicyService.delete_tenant_policy(
                session=session, group=uri, tenant_name=TenantPolicyService.TENANT_NAME
            )
            TenantPolicyService.attach_group_tenant_policy(
                session=session,
                group=uri,
                permissions=new_permissions,
                tenant_name=TenantPolicyService.TENANT_NAME,
            )

            return True

    @staticmethod
    def list_tenant_permissions():
        context = get_context()
        username = context.username
        groups = context.groups

        TenantPolicyValidationService.validate_admin_access(username, groups, 'LIST_TENANT_TEAM_PERMISSIONS')

        group_invitation_permissions = []
        with context.db_engine.scoped_session() as session:
            for p in TENANT_ALL:
                perm_obj = PermissionRepository.find_permission_by_name(
                    session=session,
                    permission_name=p,
                    permission_type=PermissionType.TENANT.name,
                )
                if perm_obj is not None:
                    group_invitation_permissions.append(perm_obj)
                else:
                    log.error(f'Permission {p} not found')
            return group_invitation_permissions

    @staticmethod
    def list_tenant_groups(data):
        context = get_context()
        username = context.username
        groups = context.groups

        RequestValidationService.validate_groups_param(groups)

        TenantPolicyValidationService.validate_admin_access(username, groups, 'LIST_TENANT_TEAMS')
        with context.db_engine.scoped_session() as session:
            return TenantPolicyRepository.list_tenant_groups(session, data)

    @staticmethod
    def has_user_tenant_permission(groups, permission_name, tenant_name):
        if TenantPolicyValidationService.is_tenant_admin(groups):
            return True

        with get_context().db_engine.scoped_session() as session:
            tenant_policy = TenantPolicyRepository.has_user_tenant_permission(
                session=session,
                groups=groups,
                permission_name=permission_name,
                tenant_name=tenant_name,
            )
            return tenant_policy is not None

    @staticmethod
    def check_user_tenant_permission(session, username: str, groups: [str], tenant_name: str, permission_name: str):
        if TenantPolicyValidationService.is_tenant_admin(groups):
            return True

        if not username or not permission_name:
            return False

        tenant_policy = TenantPolicyRepository.has_user_tenant_permission(
            session=session,
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
    ) -> TenantPolicy:
        RequestValidationService.validate_attach_tenant_policy(group, permissions, tenant_name)

        policy = TenantPolicyService.save_group_tenant_policy(session, group, tenant_name)

        TenantPolicyService.add_permission_to_group_tenant_policy(session, group, permissions, tenant_name, policy)

        return policy

    @staticmethod
    def find_tenant_policy(session, group_uri: str, tenant_name: str):
        RequestValidationService.validate_find_tenant_policy(group_uri, tenant_name)
        return TenantPolicyRepository.find_tenant_policy(session, group_uri, tenant_name)

    @staticmethod
    def save_group_tenant_policy(session, group, tenant_name):
        RequestValidationService.validate_save_tenant_policy(group, tenant_name)

        policy = TenantPolicyRepository.find_tenant_policy(session, group, tenant_name)
        if not policy:
            policy = TenantPolicy(
                principalId=group,
                principalType='GROUP',
                tenant=TenantPolicyService.get_tenant_by_name(session, tenant_name),
            )
            session.add(policy)
            session.commit()
        return policy

    @staticmethod
    def add_permission_to_group_tenant_policy(session, group, permissions, tenant_name, policy):
        RequestValidationService.validate_add_permission_to_tenant_policy_params(
            group, permissions, policy, tenant_name
        )

        for permission in permissions:
            already_associated = True
            if not group or not permission:
                already_associated = False
            else:
                already_associated = TenantPolicyRepository.has_group_tenant_permission(
                    session,
                    group_uri=group,
                    permission_name=permission,
                    tenant_name=tenant_name,
                )

            if not already_associated:
                TenantPolicyService.associate_permission_to_tenant_policy(session, policy, permission)

    @staticmethod
    def associate_permission_to_tenant_policy(session, policy, permission):
        policy_permission = TenantPolicyPermission(
            sid=policy.sid,
            permissionUri=PermissionService.get_permission_by_name(
                session, permission, PermissionType.TENANT.name
            ).permissionUri,
        )
        session.add(policy_permission)
        session.commit()

    @staticmethod
    def list_group_tenant_permissions(session, username, groups, uri, data=None, check_perm=None):
        RequestValidationService.validate_group_uri_param(groups, uri)
        TenantPolicyValidationService.validate_admin_access(username, groups, 'LIST_TENANT_TEAM_PERMISSIONS')

        return TenantPolicyService.get_tenant_policy_permissions(
            session=session,
            group_uri=uri,
            tenant_name=TenantPolicyService.TENANT_NAME,
        )

    @staticmethod
    def get_tenant_policy_permissions(session, group_uri, tenant_name):
        RequestValidationService.validate_find_tenant_policy(group_uri, tenant_name)

        policy = TenantPolicyRepository.find_tenant_policy(
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
        policy = TenantPolicyRepository.find_tenant_policy(session, group_uri=group, tenant_name=tenant_name)
        if policy:
            for permission in policy.permissions:
                session.delete(permission)
            session.delete(policy)
            session.commit()

        return True

    @staticmethod
    def get_tenant_by_name(session, tenant_name: str) -> Tenant:
        tenant = TenantRepository.find_tenant_by_name(session, tenant_name)
        if not tenant:
            raise Exception('TenantNotFound')
        return tenant

    @staticmethod
    def save_tenant(session, name: str, description: str) -> Tenant:
        tenant = TenantRepository.find_tenant_by_name(session, name)
        if tenant:
            return tenant
        else:
            tenant = Tenant(name=name, description=description if description else f'Tenant {name}')
            session.add(tenant)
            session.commit()
        return tenant

    @staticmethod
    def save_permissions_with_tenant(engine, envname=None):
        with engine.scoped_session() as session:
            log.info('Initiating permissions')
            TenantPolicyService.save_tenant(session, name=TenantPolicyService.TENANT_NAME, description='Tenant dataall')
            PermissionService.init_permissions(session)

    @staticmethod
    def has_tenant_permission(permission: str):
        """
        Decorator to check if a user has a permission to do some action.
        All the information about the user is retrieved from RequestContext
        """

        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwds):
                context = get_context()
                with context.db_engine.scoped_session() as session:
                    TenantPolicyService.check_user_tenant_permission(
                        session=session,
                        username=context.username,
                        groups=context.groups,
                        tenant_name=TenantPolicyService.TENANT_NAME,
                        permission_name=permission,
                    )
                return f(*args, **kwds)

            return wrapper

        return decorator
