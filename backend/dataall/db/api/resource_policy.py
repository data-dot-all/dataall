import logging
from typing import Optional

from sqlalchemy.sql import and_

from .. import exceptions
from .. import models
from . import Permission
from ..models.Permission import PermissionType

logger = logging.getLogger(__name__)


class ResourcePolicy:
    @staticmethod
    def check_user_resource_permission(
        session, username: str, groups: [str], resource_uri: str, permission_name: str
    ):
        resource_policy = ResourcePolicy.has_user_resource_permission(
            session=session,
            username=username,
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
    def has_user_resource_permission(
        session, username: str, groups: [str], resource_uri: str, permission_name: str
    ) -> Optional[models.ResourcePolicy]:

        if not username or not permission_name or not resource_uri:
            return None

        policy: models.ResourcePolicy = (
            session.query(models.ResourcePolicy)
            .join(
                models.ResourcePolicyPermission,
                models.ResourcePolicy.sid == models.ResourcePolicyPermission.sid,
            )
            .join(
                models.Permission,
                models.Permission.permissionUri
                == models.ResourcePolicyPermission.permissionUri,
            )
            .filter(
                and_(
                    models.ResourcePolicy.principalId.in_(groups),
                    models.ResourcePolicy.principalType == 'GROUP',
                    models.Permission.name == permission_name,
                    models.ResourcePolicy.resourceUri == resource_uri,
                )
            )
            .first()
        )

        if not policy:
            return None
        else:
            return policy

    @staticmethod
    def has_group_resource_permission(
        session, group_uri: str, resource_uri: str, permission_name: str
    ) -> Optional[models.ResourcePolicy]:

        if not group_uri or not permission_name or not resource_uri:
            return None

        policy: models.ResourcePolicy = (
            session.query(models.ResourcePolicy)
            .join(
                models.ResourcePolicyPermission,
                models.ResourcePolicy.sid == models.ResourcePolicyPermission.sid,
            )
            .join(
                models.Permission,
                models.Permission.permissionUri
                == models.ResourcePolicyPermission.permissionUri,
            )
            .filter(
                and_(
                    models.ResourcePolicy.principalId == group_uri,
                    models.ResourcePolicy.principalType == 'GROUP',
                    models.Permission.name == permission_name,
                    models.ResourcePolicy.resourceUri == resource_uri,
                )
            )
            .first()
        )

        if not policy:
            return None
        else:
            return policy

    @staticmethod
    def find_resource_policy(
        session, group_uri: str, resource_uri: str
    ) -> models.ResourcePolicy:
        if not group_uri:
            raise exceptions.RequiredParameter(param_name='group')
        if not resource_uri:
            raise exceptions.RequiredParameter(param_name='resource_uri')
        resource_policy = (
            session.query(models.ResourcePolicy)
            .filter(
                and_(
                    models.ResourcePolicy.principalId == group_uri,
                    models.ResourcePolicy.resourceUri == resource_uri,
                )
            )
            .first()
        )
        return resource_policy

    @staticmethod
    def attach_resource_policy(
        session,
        group: str,
        permissions: [str],
        resource_uri: str,
        resource_type: str,
    ) -> models.ResourcePolicy:

        ResourcePolicy.validate_attach_resource_policy_params(
            group, permissions, resource_uri, resource_type
        )

        policy = ResourcePolicy.save_resource_policy(
            session, group, resource_uri, resource_type
        )

        ResourcePolicy.add_permission_to_resource_policy(
            session, group, permissions, resource_uri, policy
        )

        return policy

    @staticmethod
    def delete_resource_policy(
        session,
        group: str,
        resource_uri: str,
        resource_type: str = None,
    ) -> bool:

        ResourcePolicy.validate_delete_resource_policy_params(group, resource_uri)
        policy = ResourcePolicy.find_resource_policy(
            session, group_uri=group, resource_uri=resource_uri
        )
        if policy:
            for permission in policy.permissions:
                session.delete(permission)
            session.delete(policy)
            session.commit()

        return True

    @staticmethod
    def validate_attach_resource_policy_params(
        group, permissions, resource_uri, resource_type
    ):
        if not group:
            raise exceptions.RequiredParameter(param_name='group')
        if not permissions:
            raise exceptions.RequiredParameter(param_name='permissions')
        if not resource_uri:
            raise exceptions.RequiredParameter(param_name='resource_uri')
        if not resource_type:
            raise exceptions.RequiredParameter(param_name='resource_type')

    @staticmethod
    def save_resource_policy(session, group, resource_uri, resource_type):
        ResourcePolicy.validate_save_resource_policy_params(
            group, resource_uri, resource_type
        )
        policy = ResourcePolicy.find_resource_policy(session, group, resource_uri)
        if not policy:
            policy = models.ResourcePolicy(
                principalId=group,
                principalType='GROUP',
                resourceUri=resource_uri,
                resourceType=resource_type,
            )
            session.add(policy)
            session.commit()
        return policy

    @staticmethod
    def validate_save_resource_policy_params(group, resource_uri, resource_type):
        if not group:
            raise exceptions.RequiredParameter(param_name='group')
        if not resource_uri:
            raise exceptions.RequiredParameter(param_name='resource_uri')
        if not resource_type:
            raise exceptions.RequiredParameter(param_name='resource_type')

    @staticmethod
    def add_permission_to_resource_policy(
        session, group, permissions, resource_uri, policy
    ):
        ResourcePolicy.validate_add_permission_to_resource_policy_params(
            group, permissions, policy, resource_uri
        )

        for permission in permissions:
            if not ResourcePolicy.has_group_resource_permission(
                session,
                group_uri=group,
                permission_name=permission,
                resource_uri=resource_uri,
            ):
                ResourcePolicy.associate_permission_to_resource_policy(
                    session, policy, permission
                )

    @staticmethod
    def validate_add_permission_to_resource_policy_params(
        group, permissions, policy, resource_uri
    ):
        if not group:
            raise exceptions.RequiredParameter(param_name='group')
        if not permissions:
            raise exceptions.RequiredParameter(param_name='permissions')
        if not resource_uri:
            raise exceptions.RequiredParameter(param_name='resource_uri')
        if not policy:
            raise exceptions.RequiredParameter(param_name='policy')

    @staticmethod
    def validate_delete_resource_policy_params(group, resource_uri):
        if not group:
            raise exceptions.RequiredParameter(param_name='group')
        if not resource_uri:
            raise exceptions.RequiredParameter(param_name='resource_uri')

    @staticmethod
    def associate_permission_to_resource_policy(session, policy, permission):
        if not policy:
            raise exceptions.RequiredParameter(param_name='policy')
        if not permission:
            raise exceptions.RequiredParameter(param_name='permission')
        policy_permission = models.ResourcePolicyPermission(
            sid=policy.sid,
            permissionUri=Permission.get_permission_by_name(
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
        policy = ResourcePolicy.find_resource_policy(
            session=session,
            group_uri=group_uri,
            resource_uri=resource_uri,
        )
        permissions = []
        for p in policy.permissions:
            permissions.append(p.permission)
        return permissions
