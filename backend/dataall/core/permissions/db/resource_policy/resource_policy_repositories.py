import logging
from typing import Optional, List

from sqlalchemy.sql import and_

from dataall.core.permissions.db.permission.permission_models import Permission
from dataall.core.permissions.db.resource_policy.resource_policy_models import ResourcePolicy, ResourcePolicyPermission

logger = logging.getLogger(__name__)


class ResourcePolicyRepository:
    @staticmethod
    def has_user_resource_permission(
        session, groups: [str], resource_uri: str, permission_name: str
    ) -> Optional[ResourcePolicy]:
        policy: ResourcePolicy = (
            session.query(ResourcePolicy)
            .join(
                ResourcePolicyPermission,
                ResourcePolicy.sid == ResourcePolicyPermission.sid,
            )
            .join(
                Permission,
                Permission.permissionUri == ResourcePolicyPermission.permissionUri,
            )
            .filter(
                and_(
                    ResourcePolicy.principalId.in_(groups),
                    ResourcePolicy.principalType == 'GROUP',
                    Permission.name == permission_name,
                    ResourcePolicy.resourceUri == resource_uri,
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
    ) -> Optional[ResourcePolicy]:
        policy: ResourcePolicy = (
            session.query(ResourcePolicy)
            .join(
                ResourcePolicyPermission,
                ResourcePolicy.sid == ResourcePolicyPermission.sid,
            )
            .join(
                Permission,
                Permission.permissionUri == ResourcePolicyPermission.permissionUri,
            )
            .filter(
                and_(
                    ResourcePolicy.principalId == group_uri,
                    ResourcePolicy.principalType == 'GROUP',
                    Permission.name == permission_name,
                    ResourcePolicy.resourceUri == resource_uri,
                )
            )
            .first()
        )

        if not policy:
            return None
        else:
            return policy

    @staticmethod
    def query_all_resource_policies(
        session, group_uri: str, resource_uri: str, resource_type: str = None, permissions: List[str] = None
    ):
        resource_policy = session.query(ResourcePolicy).filter(
            ResourcePolicy.resourceUri == resource_uri,
        )
        if group_uri is not None:
            resource_policy = resource_policy.filter(
                ResourcePolicy.principalId == group_uri,
            )

        if resource_type is not None:
            resource_policy = resource_policy.filter(
                ResourcePolicy.resourceType == resource_type,
            )

        if permissions is not None:
            resource_policy = (
                resource_policy.join(
                    ResourcePolicyPermission,
                    ResourcePolicy.sid == ResourcePolicyPermission.sid,
                )
                .join(
                    Permission,
                    ResourcePolicyPermission.permissionUri == Permission.permissionUri,
                )
                .filter(Permission.name.in_(permissions))
            )

        return resource_policy

    @staticmethod
    def find_resource_policy(session, group_uri: str, resource_uri: str, resource_type: str = None) -> ResourcePolicy:
        resource_policy = ResourcePolicyRepository.query_all_resource_policies(
            session, group_uri, resource_uri, resource_type
        )
        return resource_policy.first()

    @staticmethod
    def find_all_resource_policies(
        session, group_uri: str, resource_uri: str, resource_type: str = None, permissions: List[str] = None
    ) -> List[ResourcePolicy]:
        resource_policy = ResourcePolicyRepository.query_all_resource_policies(
            session, group_uri, resource_uri, resource_type, permissions
        )
        return resource_policy.all()
