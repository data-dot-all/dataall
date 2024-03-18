"""
DAO layer that encapsulates the logic and interaction with the database for warehouses
Provides the API to retrieve / update / delete warehouse connections, consumers
"""

from sqlalchemy import or_
from sqlalchemy.sql import and_
from sqlalchemy.orm import Query

from dataall.base.db import paginate
from dataall.modules.warehouses.db.warehouse_models import WarehouseConsumer, WarehouseConnection
# from dataall.core.environment.services.environment_resource_manager import EnvironmentResource


class WarehouseRepository:  # TODO: DECIDE: SHOULD IT BE AN EnvironmentResource?
    """DAO layer for warehouses"""

    _DEFAULT_PAGE = 1
    _DEFAULT_PAGE_SIZE = 10

    def __init__(self, session):
        self._session = session

    def save_item(self, item):
        """Save connection or consumer to the database"""
        self._session.add(item)
        self._session.commit()

    def delete_item(self, item):
        """Delete connection or consumer to the database"""
        self._session.delete(item)
        self._session.commit()

    def find_warehouse_connection(self, uri):
        """Finds a warehouse connection. Returns None if it doesn't exist"""
        return self._session.query(WarehouseConnection).get(uri)

    def find_warehouse_consumer(self, uri):
        """Finds a warehouse consumer. Returns None if it doesn't exist"""
        return self._session.query(WarehouseConsumer).get(uri)

    def paginated_user_connections(self, username, groups, filter=None) -> dict:
        """Returns a page of user warehouse connections"""
        return paginate(
            query=self._query_user_connections(username, groups, filter),
            page=filter.get('page', WarehouseRepository._DEFAULT_PAGE),
            page_size=filter.get('pageSize', WarehouseRepository._DEFAULT_PAGE_SIZE),
        ).to_dict()

    def _query_user_connections(self, username, groups, filter) -> Query:
        query = self._session.query(WarehouseConnection).filter(
            or_(
                WarehouseConnection.SamlAdminGroupName.in_(groups),
            )
        )
        # if filter and filter.get('term'):
        # TODO: ADD FILTERS IN VIEW: WAREHOUSETYPE, TEAM, ....
        return query

    def paginated_user_consumers(self, username, groups, filter=None) -> dict:
        """Returns a page of user warehouse consumers"""
        return paginate(
            query=self._query_user_consumers(username, groups, filter),
            page=filter.get('page', WarehouseRepository._DEFAULT_PAGE),
            page_size=filter.get('pageSize', WarehouseRepository._DEFAULT_PAGE_SIZE),
        ).to_dict()

    def _query_user_consumers(self, username, groups, filter) -> Query:
        query = self._session.query(WarehouseConsumer).filter(
            or_(
                WarehouseConsumer.SamlAdminGroupName.in_(groups),
            )
        )
        # if filter and filter.get('term'):
        # TODO: ADD FILTERS IN VIEW: WAREHOUSETYPE, TEAM, ....
        return query
