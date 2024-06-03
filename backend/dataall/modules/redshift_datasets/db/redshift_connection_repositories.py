import logging

from sqlalchemy import and_, or_
from sqlalchemy.orm import Query
from dataall.core.environment.db.environment_models import Environment
from dataall.core.organizations.db.organization_repositories import OrganizationRepository
from dataall.base.db import paginate
from dataall.base.db.exceptions import ObjectNotFound
from dataall.modules.redshift_datasets.db.redshift_models import RedshiftConnection

logger = logging.getLogger(__name__)


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
    def find_redshift_connection(session, uri) -> RedshiftConnection:
        """Find Redshift Connection by URI"""
        return session.query(RedshiftConnection).get(uri)

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
        if filter and filter.get('term'):
            query = query.filter(
                or_(
                    RedshiftConnection.description.ilike(filter.get('term') + '%%'),
                    RedshiftConnection.label.ilike(filter.get('term') + '%%'),
                )
            )
        return query.order_by(RedshiftConnection.label)

    @staticmethod
    def paginated_user_redshift_connections(session, username, groups, filter={}) -> dict:
        """Returns a page of sagemaker studio users for a data.all user"""
        return paginate(
            query=RedshiftConnectionRepository._query_user_redshift_connections(session, username, groups, filter),
            page=filter.get('page', RedshiftConnectionRepository._DEFAULT_PAGE),
            page_size=filter.get('pageSize', RedshiftConnectionRepository._DEFAULT_PAGE_SIZE),
        ).to_dict()