import logging

from dataall.core.permissions.api.enums import PermissionType
from dataall.core.permissions.db.permission.permission_models import Permission

logger = logging.getLogger(__name__)


class PermissionRepository:
    @staticmethod
    def find_permission_by_name(session, permission_name: str, permission_type: str) -> Permission:
        if permission_name:
            permission = (
                session.query(Permission)
                .filter(
                    Permission.name == permission_name,
                    Permission.type == permission_type,
                )
                .first()
            )
            return permission

    @staticmethod
    def count_resource_permissions(session):
        return session.query(Permission).filter(Permission.type == PermissionType.RESOURCE.name).count()

    @staticmethod
    def count_tenant_permissions(session):
        return session.query(Permission).filter(Permission.type == PermissionType.TENANT.name).count()
