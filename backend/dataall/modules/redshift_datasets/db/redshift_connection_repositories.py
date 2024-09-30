import logging

from sqlalchemy import or_
from sqlalchemy.orm import Query
from dataall.base.db import exceptions
from dataall.core.environment.services.environment_resource_manager import EnvironmentResource
from dataall.base.db import paginate
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
        query = session.query(RedshiftConnection).filter(
            or_(
                RedshiftConnection.owner == username,
                RedshiftConnection.SamlGroupName.in_(groups),
            )
        )
        if filter and filter.get('environmentUri'):
            query = query.filter(RedshiftConnection.environmentUri == filter.get('environmentUri'))
        if filter and filter.get('groupUri'):
            query = query.filter(RedshiftConnection.SamlGroupName == filter.get('groupUri'))
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
