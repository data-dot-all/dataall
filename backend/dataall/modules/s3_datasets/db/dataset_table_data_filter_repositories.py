import logging

from dataall.base.db import exceptions
from dataall.modules.s3_datasets.db.dataset_models import DatasetTableDataFilter
from dataall.modules.s3_datasets.services.dataset_table_data_filter_enums import DataFilterType
from dataall.base.db import paginate

logger = logging.getLogger(__name__)


class DatasetTableDataFilterRepository:
    @staticmethod
    def build_data_filter(session, username, table_uri, data):
        return DatasetTableDataFilter(
            tableUri=table_uri,
            label=data.get('filterName'),
            filterType=data.get('filterType'),
            description=data.get('description'),
            rowExpression=data.get('rowExpression') if data.get('filterType') == DataFilterType.ROW.value else None,
            includedCols=data.get('includedCols') if data.get('filterType') == DataFilterType.COLUMN.value else None,
            owner=username,
        )

    @staticmethod
    def save(session, data_filter: DatasetTableDataFilter):
        session.add(data_filter)
        session.commit()

    @staticmethod
    def delete(session, data_filter: DatasetTableDataFilter):
        session.delete(data_filter)
        return True

    @staticmethod
    def get_data_filter_by_uri(session, filter_uri):
        data_filter: DatasetTableDataFilter = session.query(DatasetTableDataFilter).get(filter_uri)
        if not data_filter:
            raise exceptions.ObjectNotFound('DatasetTableDataFilter', filter_uri)
        return data_filter

    @staticmethod
    def _list_data_filters(session, table_uri, data):
        query = (
            session.query(DatasetTableDataFilter)
            .filter(DatasetTableDataFilter.tableUri == table_uri)
            .order_by(DatasetTableDataFilter.created.desc())
        )

        if filterUris := data.get('filterUris'):
            query = query.filter(DatasetTableDataFilter.filterUri.in_(filterUris))

        if term := data.get('term'):
            query = query.filter(DatasetTableDataFilter.name.ilike('%' + term + '%'))

        return query

    @staticmethod
    def paginated_data_filters(session, table_uri, data) -> dict:
        query = DatasetTableDataFilterRepository._list_data_filters(session, table_uri, data)
        return paginate(query=query, page_size=data.get('pageSize', 10), page=data.get('page', 1)).to_dict()

    @staticmethod
    def list_data_filters(session, table_uri):
        query = DatasetTableDataFilterRepository._list_data_filters(session, table_uri, {})
        return query.all()
