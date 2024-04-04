import logging
from collections import Counter

from sqlalchemy.orm import Session

from dataall.base.db import exceptions
from dataall.core.permissions.api.enums import PermissionType
from dataall.core.permissions.db.permission.permission_models import Permission
from dataall.core.permissions.db.permission.permission_repositories import PermissionRepository
from dataall.core.permissions.services.resources_permissions import RESOURCES_ALL_WITH_DESC
from dataall.core.permissions.services.tenant_permissions import TENANT_ALL_WITH_DESC

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
    def check_and_save_permissions(
        session: Session, db_perms: [str], app_perms: dict[str, str], perm_type: PermissionType
    ):
        perms = []
        logger.info(f'db  perms {sorted(db_perms)}')
        logger.info(f'app perms {sorted(app_perms)}')

        for perm, freq in Counter(db_perms).items():
            if freq > 1:
                logger.warning('%50s permission appears %3d times in the db', perm, freq)

        for obsolete_param in set(db_perms) - set(app_perms.keys()):
            logger.warning('obsolete parameter %s', obsolete_param)

        missing_perms = set(app_perms.keys()) - set(db_perms)
        for perm in missing_perms:
            logger.info('inserting %50s permission', perm)
            perms.append(
                PermissionService.save_permission(
                    session,
                    name=perm,
                    description=app_perms[perm],
                    permission_type=perm_type.name,
                )
            )
        session.commit()
        return perms

    @staticmethod
    def init_permissions(session: Session) -> [str]:
        return PermissionService.check_and_save_permissions(
            session,
            [
                perm.name
                for perm in session.query(Permission).filter(Permission.type == PermissionType.RESOURCE.name).all()
            ],
            RESOURCES_ALL_WITH_DESC,
            PermissionType.RESOURCE,
        ) + PermissionService.check_and_save_permissions(
            session,
            [
                perm.name
                for perm in session.query(Permission).filter(Permission.type == PermissionType.TENANT.name).all()
            ],
            TENANT_ALL_WITH_DESC,
            PermissionType.TENANT,
        )
