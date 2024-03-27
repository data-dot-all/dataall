from dataall.core.permissions.api.enums import PermissionType
from dataall.core.permissions.db.permission.permission_repositories import PermissionRepository
from dataall.base.db import exceptions
from dataall.core.permissions.db.permission.permission_models import Permission
from dataall.core.permissions.services.core_permissions import RESOURCES_ALL_WITH_DESC, TENANT_ALL_WITH_DESC

import logging

logger = logging.getLogger(__name__)


class PermissionService:
    @staticmethod
    def get_permission_by_name(session, permission_name: str, permission_type: str) -> Permission:
        if not permission_name:
            raise exceptions.RequiredParameter(param_name='permission_name')
        permission = PermissionRepository.find_permission_by_name(session, permission_name, permission_type)
        if not permission:
            raise exceptions.ObjectNotFound('Permission', permission_name)
        return permission

    @staticmethod
    def save_permission(session, name: str, description: str, permission_type: str) -> Permission:
        if not name:
            raise exceptions.RequiredParameter('name')
        if not type:
            raise exceptions.RequiredParameter('permission_type')
        permission = PermissionRepository.find_permission_by_name(session, name, permission_type)
        if permission:
            logger.info(f'Permission {permission.name} already exists')
        else:
            permission = Permission(
                name=name,
                description=description if description else f'Allows {name}',
                type=permission_type,
            )
            session.add(permission)
        return permission

    @staticmethod
    def init_permissions(session):
        perms = []
        count_resource_permissions = PermissionRepository.count_resource_permissions(session)

        logger.debug(
            f'count_resource_permissions: {count_resource_permissions}, RESOURCES_ALL: {len(RESOURCES_ALL_WITH_DESC)}'
        )

        if count_resource_permissions < len(RESOURCES_ALL_WITH_DESC):
            for name, desc in RESOURCES_ALL_WITH_DESC.items():
                perms.append(
                    PermissionService.save_permission(
                        session,
                        name=name,
                        description=desc,
                        permission_type=PermissionType.RESOURCE.name,
                    )
                )
                logger.info(f'Saved permission {name} successfully')
            logger.info(f'Saved {len(perms)} resource permissions successfully')

        count_tenant_permissions = PermissionRepository.count_tenant_permissions(session)

        logger.debug(f'count_tenant_permissions: {count_tenant_permissions}, TENANT_ALL: {len(TENANT_ALL_WITH_DESC)}')

        if count_tenant_permissions < len(TENANT_ALL_WITH_DESC):
            for name, desc in TENANT_ALL_WITH_DESC.items():
                perms.append(
                    PermissionService.save_permission(
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
