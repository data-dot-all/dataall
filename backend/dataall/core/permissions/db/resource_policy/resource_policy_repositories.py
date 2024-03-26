import logging
from typing import Optional

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
    def find_resource_policy(session, group_uri: str, resource_uri: str) -> ResourcePolicy:
        resource_policy = (
            session.query(ResourcePolicy)
            .filter(
                and_(
                    ResourcePolicy.principalId == group_uri,
                    ResourcePolicy.resourceUri == resource_uri,
                )
            )
            .first()
        )
        return resource_policy
