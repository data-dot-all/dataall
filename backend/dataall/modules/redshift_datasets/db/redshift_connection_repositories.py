import logging

from sqlalchemy import or_, and_, func
from sqlalchemy.orm import Query
from dataall.base.db import exceptions, paginate
from dataall.core.environment.services.environment_resource_manager import EnvironmentResource
from dataall.core.permissions.db.permission.permission_models import Permission
from dataall.core.permissions.db.resource_policy.resource_policy_models import ResourcePolicy, ResourcePolicyPermission
from dataall.core.environment.db.environment_models import EnvironmentGroup
from dataall.modules.redshift_datasets.db.redshift_models import RedshiftConnection
from dataall.modules.redshift_datasets.services.redshift_enums import RedshiftConnectionTypes

logger = logging.getLogger(__name__)


class RedshiftConnectionEnvironmentResource(EnvironmentResource):
    """Actions performed on any environment resource on environment operations"""

    @staticmethod
    def delete_env(session, environment):
        RedshiftConnectionRepository.delete_all_environment_connections(session, environment.environmentUri)


class RedshiftConnectionRepository:
    """DAO layer for Redshift Connections"""

    _DEFAULT_PAGE = 1
    _DEFAULT_PAGE_SIZE = 10

    @staticmethod
    def save_redshift_connection(session, connection):
        """Save Redshift Connection to the database"""
        session.add(connection)
        session.commit()

    @staticmethod
    def get_redshift_connection(session, uri) -> RedshiftConnection:
        """Find Redshift Connection by URI"""
        connection = session.query(RedshiftConnection).get(uri)
        if not connection:
            raise exceptions.ObjectNotFound('RedshiftConnection', uri)
        return connection

    @staticmethod
    def _query_user_redshift_connections(session, username, groups, filter) -> Query:
        query = (
            session.query(RedshiftConnection)
            .join(ResourcePolicy, ResourcePolicy.resourceUri == RedshiftConnection.connectionUri)
            .filter(
                or_(
                    RedshiftConnection.owner == username,
                    RedshiftConnection.SamlGroupName.in_(groups),
                    ResourcePolicy.principalId.in_(groups),
                )
            )
        )
        if filter and filter.get('environmentUri'):
            query = query.filter(RedshiftConnection.environmentUri == filter.get('environmentUri'))
        if filter and filter.get('groupUri'):
            query = query.filter(
                or_(
                    RedshiftConnection.SamlGroupName == filter.get('groupUri'),
                    ResourcePolicy.principalId == filter.get('groupUri'),
                )
            )
        if filter and filter.get('connectionType'):
            query = query.filter(RedshiftConnection.connectionType == filter.get('connectionType'))
        if filter and filter.get('term'):
            query = query.filter(
                or_(
                    RedshiftConnection.description.ilike(filter.get('term') + '%%'),
                    RedshiftConnection.label.ilike(filter.get('term') + '%%'),
                )
            )
        return query.order_by(RedshiftConnection.label)

    @staticmethod
    def list_environment_redshift_connections(session, environment_uri):
        query = session.query(RedshiftConnection).filter(RedshiftConnection.environmentUri == environment_uri)
        return query.order_by(RedshiftConnection.label).all()

    @staticmethod
    def get_namespace_admin_connection(session, environment_uri, namespace_id):
        query = session.query(RedshiftConnection).filter(
            RedshiftConnection.environmentUri == environment_uri,
            RedshiftConnection.nameSpaceId == namespace_id,
            RedshiftConnection.connectionType == RedshiftConnectionTypes.ADMIN.value,
        )
        return query.first()

    @staticmethod
    def paginated_user_redshift_connections(session, username, groups, filter={}) -> dict:
        return paginate(
            query=RedshiftConnectionRepository._query_user_redshift_connections(session, username, groups, filter),
            page=filter.get('page', RedshiftConnectionRepository._DEFAULT_PAGE),
            page_size=filter.get('pageSize', RedshiftConnectionRepository._DEFAULT_PAGE_SIZE),
        ).to_dict()

    @staticmethod
    def delete_all_environment_connections(session, environment_uri):
        session.query(RedshiftConnection).filter(RedshiftConnection.environmentUri == environment_uri).delete()

    @staticmethod
    def _query_redshift_connection_group_permissions(session, connection_uri, permissions, filter) -> Query:
        query = (
            session.query(
                ResourcePolicy.principalId.label('groupUri'),
                func.array_agg(
                    func.json_build_object('name', Permission.name, 'description', Permission.description)
                ).label('permissions'),
            )
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
                    ResourcePolicy.principalType == 'GROUP',
                    ResourcePolicy.resourceUri == connection_uri,
                    ResourcePolicy.resourceType == RedshiftConnection.__name__,
                    Permission.name.in_(permissions),
                )
            )
            .group_by(ResourcePolicy.principalId)
        )

        if filter and filter.get('term'):
            query = query.filter(
                ResourcePolicy.principalId.ilike(filter.get('term') + '%%'),
            )
        return query.order_by(ResourcePolicy.principalId)

    @staticmethod
    def paginated_redshift_connection_group_permissions(session, connection_uri, permissions, filter) -> dict:
        return paginate(
            query=RedshiftConnectionRepository._query_redshift_connection_group_permissions(
                session, connection_uri, permissions, filter
            ),
            page=filter.get('page', RedshiftConnectionRepository._DEFAULT_PAGE),
            page_size=filter.get('pageSize', RedshiftConnectionRepository._DEFAULT_PAGE_SIZE),
        ).to_dict()

    @staticmethod
    def list_redshift_connection_group_no_permissions(session, connection_uri, environment_uri, filter) -> list[str]:
        groups_with_permissions = (
            session.query(ResourcePolicy.principalId).filter(ResourcePolicy.resourceUri == connection_uri).all()
        )

        groups_with_permissions = [g[0] for g in groups_with_permissions]
        logger.info(f'Groups with permissions: {groups_with_permissions}')

        groups_without_permission = (
            session.query(EnvironmentGroup.groupUri.label('groupUri'))
            .filter(
                and_(
                    EnvironmentGroup.environmentUri == environment_uri,
                    EnvironmentGroup.groupUri.notin_(groups_with_permissions),
                )
            )
            .order_by(EnvironmentGroup.groupUri)
            .all()
        )
        return [g[0] for g in groups_without_permission]
