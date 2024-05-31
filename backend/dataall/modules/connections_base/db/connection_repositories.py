import logging

from sqlalchemy import or_
from sqlalchemy.orm import Query
from dataall.base.db import paginate
from dataall.modules.connections_base.db.connection_models import Connection

logger = logging.getLogger(__name__)


class ConnectionRepository:
    """DAO layer for Connections"""

    _DEFAULT_PAGE = 1
    _DEFAULT_PAGE_SIZE = 10

    @staticmethod
    def _query_user_connections(session, username, groups, filter) -> Query:
        query = session.query(Connection).filter(
            or_(
                Connection.owner == username,
                Connection.SamlGroupName.in_(groups),
            )
        )
        if filter and filter.get('environmentUri'):
            query = query.filter(Connection.environmentUri == filter.get('environmentUri'))
        if filter and filter.get('term'):
            query = query.filter(
                or_(
                    Connection.description.ilike(filter.get('term') + '%%'),
                    Connection.label.ilike(filter.get('term') + '%%'),
                )
            )
        return query.order_by(Connection.label)

    @staticmethod
    def paginated_user_connections(session, username, groups, filter={}) -> dict:
        """Returns a page of sagemaker studio users for a data.all user"""
        return paginate(
            query=ConnectionRepository._query_user_connections(session, username, groups, filter),
            page=filter.get('page', ConnectionRepository._DEFAULT_PAGE),
            page_size=filter.get('pageSize', ConnectionRepository._DEFAULT_PAGE_SIZE),
        ).to_dict()