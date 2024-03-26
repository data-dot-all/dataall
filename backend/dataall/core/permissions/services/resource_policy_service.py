from dataall.core.permissions.api.enums import PermissionType
from dataall.core.permissions.db.resource_policy.resource_policy_repositories import ResourcePolicyRepository
from dataall.base.db import exceptions
from dataall.core.permissions.db.resource_policy.resource_policy_models import ResourcePolicy, ResourcePolicyPermission
from dataall.core.permissions.services.permission_service import PermissionService


class ResourcePolicyRequestValidationService:
    @staticmethod
    def validate_find_or_delete_resource_policy_params(group_uri, resource_uri):
        if not group_uri:
            raise exceptions.RequiredParameter(param_name='group')
        if not resource_uri:
            raise exceptions.RequiredParameter(param_name='resource_uri')

    @staticmethod
    def validate_save_resource_policy_params(group, resource_uri, resource_type):
        if not group:
            raise exceptions.RequiredParameter(param_name='group')
        if not resource_uri:
            raise exceptions.RequiredParameter(param_name='resource_uri')
        if not resource_type:
            raise exceptions.RequiredParameter(param_name='resource_type')

    @staticmethod
    def validate_add_permission_to_resource_policy_params(group, permissions, policy, resource_uri):
        if not group:
            raise exceptions.RequiredParameter(param_name='group')
        if not permissions:
            raise exceptions.RequiredParameter(param_name='permissions')
        if not resource_uri:
            raise exceptions.RequiredParameter(param_name='resource_uri')
        if not policy:
            raise exceptions.RequiredParameter(param_name='policy')

    @staticmethod
    def validate_attach_resource_policy_params(group, permissions, resource_uri, resource_type):
        if not group:
            raise exceptions.RequiredParameter(param_name='group')
        if not permissions:
            raise exceptions.RequiredParameter(param_name='permissions')
        if not resource_uri:
            raise exceptions.RequiredParameter(param_name='resource_uri')
        if not resource_type:
            raise exceptions.RequiredParameter(param_name='resource_type')


class ResourcePolicyService:
    @staticmethod
    def check_user_resource_permission(session, username: str, groups: [str], resource_uri: str, permission_name: str):
        resource_policy = None
        if username and permission_name and resource_uri:
            resource_policy = ResourcePolicyRepository.has_user_resource_permission(
                session=session,
                groups=groups,
                permission_name=permission_name,
                resource_uri=resource_uri,
            )

        if not resource_policy:
            raise exceptions.ResourceUnauthorized(
                username=username,
                action=permission_name,
                resource_uri=resource_uri,
            )
        else:
            return resource_policy

    @staticmethod
    def delete_resource_policy(
        session,
        group: str,
        resource_uri: str,
        resource_type: str = None,
    ) -> bool:
        ResourcePolicyRequestValidationService.validate_find_or_delete_resource_policy_params(group, resource_uri)
        policy = ResourcePolicyRepository.find_resource_policy(session, group_uri=group, resource_uri=resource_uri)
        if policy:
            for permission in policy.permissions:
                session.delete(permission)
            session.delete(policy)
            session.commit()

        return True

    @staticmethod
    def update_resource_policy(
        session, resource_uri: str, resource_type: str, old_group: str, new_group: str, new_permissions: [str]
    ) -> ResourcePolicy:
        ResourcePolicyService.delete_resource_policy(
            session=session,
            group=old_group,
            resource_uri=resource_uri,
            resource_type=resource_type,
        )
        return ResourcePolicyService.attach_resource_policy(
            session=session,
            group=new_group,
            resource_uri=resource_uri,
            permissions=new_permissions,
            resource_type=resource_type,
        )

    @staticmethod
    def attach_resource_policy(
        session,
        group: str,
        permissions: [str],
        resource_uri: str,
        resource_type: str,
    ) -> ResourcePolicy:
        ResourcePolicyRequestValidationService.validate_attach_resource_policy_params(
            group, permissions, resource_uri, resource_type
        )

        policy = ResourcePolicyService.save_resource_policy(session, group, resource_uri, resource_type)

        ResourcePolicyService.add_permission_to_resource_policy(session, group, permissions, resource_uri, policy)

        return policy

    @staticmethod
    def save_resource_policy(session, group, resource_uri, resource_type):
        ResourcePolicyRequestValidationService.validate_save_resource_policy_params(group, resource_uri, resource_type)
        policy = ResourcePolicyRepository.find_resource_policy(session, group, resource_uri)
        if not policy:
            policy = ResourcePolicy(
                principalId=group,
                principalType='GROUP',
                resourceUri=resource_uri,
                resourceType=resource_type,
            )
            session.add(policy)
            session.commit()
        return policy

    @staticmethod
    def add_permission_to_resource_policy(session, group, permissions, resource_uri, policy):
        ResourcePolicyRequestValidationService.validate_add_permission_to_resource_policy_params(
            group, permissions, policy, resource_uri
        )

        for permission in permissions:
            has_permissions = None
            if group and permission and resource_uri:
                has_permissions = ResourcePolicyRepository.has_group_resource_permission(
                    session,
                    group_uri=group,
                    permission_name=permission,
                    resource_uri=resource_uri,
                )

            if not has_permissions:
                ResourcePolicyService.associate_permission_to_resource_policy(session, policy, permission)

    @staticmethod
    def associate_permission_to_resource_policy(session, policy, permission):
        if not policy:
            raise exceptions.RequiredParameter(param_name='policy')
        if not permission:
            raise exceptions.RequiredParameter(param_name='permission')
        policy_permission = ResourcePolicyPermission(
            sid=policy.sid,
            permissionUri=PermissionService.get_permission_by_name(
                session, permission, permission_type=PermissionType.RESOURCE.name
            ).permissionUri,
        )
        session.add(policy_permission)
        session.commit()

    @staticmethod
    def get_resource_policy_permissions(session, group_uri, resource_uri):
        if not group_uri:
            raise exceptions.RequiredParameter(param_name='group_uri')
        if not resource_uri:
            raise exceptions.RequiredParameter(param_name='resource_uri')
        policy = ResourcePolicyRepository.find_resource_policy(
            session=session,
            group_uri=group_uri,
            resource_uri=resource_uri,
        )
        permissions = []
        for p in policy.permissions:
            permissions.append(p.permission)
        return permissions
