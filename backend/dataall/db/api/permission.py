import logging

from sqlalchemy import or_

from ..paginator import paginate
from .. import models, exceptions, permissions
from ..models.Permission import PermissionType

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
    def paginated_tenant_permissions(session, data) -> dict:
        if not data:
            data = dict()
        data['type'] = PermissionType.TENANT
        return Permission.paginated_permissions(session, data)

    @staticmethod
    def paginated_resource_permissions(session, data) -> dict:
        if not data:
            data = dict()
        data['type'] = PermissionType.RESOURCE
        return Permission.paginated_permissions(session, data)

    @staticmethod
    def paginated_permissions(session, data) -> dict:
        query = session.query(models.Permission)
        if data:
            if data.get('type'):
                query = query.filter(models.Permission.type == data['type'])
            if data.get('term'):
                term = data['term']
                query = query.filter(
                    or_(
                        models.Permission.name.ilike('%' + term + '%'),
                        models.Permission.description.ilike('%' + term + '%'),
                    )
                )
        return paginate(
            query=query,
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    def init_permissions(session):
        perms = []
        count_resource_permissions = (
            session.query(models.Permission)
            .filter(models.Permission.type == PermissionType.RESOURCE.name)
            .count()
        )
        if count_resource_permissions < len(permissions.RESOURCES_ALL):
            for p in permissions.RESOURCES_ALL:
                description = p
                if p == permissions.CREATE_DATASET:
                    description = 'Create datasets on this environment'
                if p == permissions.CREATE_DASHBOARD:
                    description = 'Create dashboards on this environment'
                if p == permissions.CREATE_NOTEBOOK:
                    description = 'Create notebooks on this environment'
                if p == permissions.CREATE_REDSHIFT_CLUSTER:
                    description = 'Create Redshift clusters on this environment'
                if p == permissions.CREATE_SGMSTUDIO_NOTEBOOK:
                    description = 'Manage ML Studio profiles on this environment'
                if p == permissions.INVITE_ENVIRONMENT_GROUP:
                    description = 'Invite other teams to this environment'
                if p == permissions.CREATE_SHARE_OBJECT:
                    description = 'Request datasets access for this environment'
                if p == permissions.CREATE_PIPELINE:
                    description = 'Create pipelines on this environment'
                if p == permissions.CREATE_NETWORK:
                    description = 'Create networks on this environment'
                perms.append(
                    Permission.save_permission(
                        session,
                        name=p,
                        description=description,
                        permission_type=PermissionType.RESOURCE.name,
                    )
                )
                print(f'Saved permission {p} successfully')

        print(f'Saved {len(perms)} resource permissions successfully')

        count_tenant_permissions = (
            session.query(models.Permission)
            .filter(models.Permission.type == PermissionType.TENANT.name)
            .count()
        )
        if count_tenant_permissions < len(permissions.TENANT_ALL):
            for p in permissions.TENANT_ALL:
                description = p
                if p == permissions.MANAGE_DASHBOARDS:
                    description = 'Manage dashboards'
                if p == permissions.MANAGE_DATASETS:
                    description = 'Manage datasets'
                if p == permissions.MANAGE_NOTEBOOKS:
                    description = 'Manage notebooks'
                if p == permissions.MANAGE_REDSHIFT_CLUSTERS:
                    description = 'Manage Redshift clusters'
                if p == permissions.MANAGE_GLOSSARIES:
                    description = 'Manage glossaries'
                if p == permissions.MANAGE_WORKSHEETS:
                    description = 'Manage worksheets'
                if p == permissions.MANAGE_ENVIRONMENTS:
                    description = 'Manage environments'
                if p == permissions.MANAGE_GROUPS:
                    description = 'Manage teams'
                if p == permissions.MANAGE_PIPELINES:
                    description = 'Manage pipelines'
                if p == permissions.MANAGE_ORGANIZATIONS:
                    description = 'Manage organizations'
                perms.append(
                    Permission.save_permission(
                        session,
                        name=p,
                        description=description,
                        permission_type=PermissionType.TENANT.name,
                    )
                )
                print(f'Saved permission {p} successfully')
            print(f'Saved {len(perms)} permissions successfully')
            session.commit()
        return perms
