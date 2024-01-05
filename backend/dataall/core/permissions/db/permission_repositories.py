import logging

from dataall.core.permissions.db.permission_models import PermissionType
from dataall.base.db import exceptions
from dataall.core.permissions import permissions
from dataall.core.permissions.db import permission_models as models


logger = logging.getLogger(__name__)


class Permission:
    @staticmethod
    def find_permission_by_name(
        session, permission_name: str, permission_type: str
    ) -> models.Permission:
        if permission_name:
            permission = (
                session.query(models.Permission)
                .filter(
                    models.Permission.name == permission_name,
                    models.Permission.type == permission_type,
                )
                .first()
            )
            return permission

    @staticmethod
    def get_permission_by_name(
        session, permission_name: str, permission_type: str
    ) -> models.Permission:
        if not permission_name:
            raise exceptions.RequiredParameter(param_name='permission_name')
        permission = Permission.find_permission_by_name(
            session, permission_name, permission_type
        )
        if not permission:
            raise exceptions.ObjectNotFound('Permission', permission_name)
        return permission

    @staticmethod
    def find_permission_by_uri(
        session, permission_uri: str, permission_type: str
    ) -> models.Permission:
        if permission_uri:
            permission = (
                session.query(models.Permission)
                .filter(
                    models.Permission.permissionUri == permission_uri,
                    models.Permission.type == permission_type,
                )
                .first()
            )
            return permission

    @staticmethod
    def get_permission_by_uri(
        session, permission_uri: str, permission_type: str
    ) -> models.Permission:
        if not permission_uri:
            raise exceptions.RequiredParameter(param_name='permission_uri')
        permission = Permission.find_permission_by_uri(
            session, permission_uri, permission_type
        )
        if not permission:
            raise exceptions.ObjectNotFound('Permission', permission_uri)
        return permission

    @staticmethod
    def save_permission(
        session, name: str, description: str, permission_type: str
    ) -> models.Permission:
        if not name:
            raise exceptions.RequiredParameter('name')
        if not type:
            raise exceptions.RequiredParameter('permission_type')
        permission = Permission.find_permission_by_name(session, name, permission_type)
        if permission:
            logger.info(f'Permission {permission.name} already exists')
        else:
            permission = models.Permission(
                name=name,
                description=description if description else f'Allows {name}',
                type=permission_type,
            )
            session.add(permission)
        return permission

    @staticmethod
    def init_permissions(session):
        perms = []
        count_resource_permissions = (
            session.query(models.Permission)
            .filter(models.Permission.type == PermissionType.RESOURCE.name)
            .count()
        )

        logger.error(f'count_resource_permissions: {count_resource_permissions}, RESOURCES_ALL: {len(permissions.RESOURCES_ALL_WITH_DESC)}')

        if count_resource_permissions < len(permissions.RESOURCES_ALL_WITH_DESC):
            for name, desc in permissions.RESOURCES_ALL_WITH_DESC.items():
                perms.append(
                    Permission.save_permission(
                        session,
                        name=name,
                        description=desc,
                        permission_type=PermissionType.RESOURCE.name,
                    )
                )
                logger.error(f'Saved permission {name} successfully')
            logger.error(f'Saved {len(perms)} resource permissions successfully')
            session.commit()

        count_tenant_permissions = (
            session.query(models.Permission)
            .filter(models.Permission.type == PermissionType.TENANT.name)
            .count()
        )

        logger.error(f'count_tenant_permissions: {count_tenant_permissions}, TENANT_ALL: {len(permissions.TENANT_ALL_WITH_DESC)}')

        if count_tenant_permissions < len(permissions.TENANT_ALL_WITH_DESC):
            for name, desc in permissions.TENANT_ALL_WITH_DESC.items():
                perms.append(
                    Permission.save_permission(
                        session,
                        name=name,
                        description=desc,
                        permission_type=PermissionType.TENANT.name,
                    )
                )
                logger.info(f'Saved permission {name} successfully')
            logger.info(f'Saved {len(perms)} permissions successfully')
            session.commit()
        return perms
