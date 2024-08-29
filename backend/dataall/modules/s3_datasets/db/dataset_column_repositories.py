from operator import or_

from dataall.base.db import paginate
from dataall.base.db.exceptions import ObjectNotFound
from dataall.modules.s3_datasets.db.dataset_models import DatasetTableColumn


class DatasetColumnRepository:
    @staticmethod
    def get_column(session, column_uri) -> DatasetTableColumn:
        column = session.query(DatasetTableColumn).get(column_uri)
        if not column:
            raise ObjectNotFound('Column', column_uri)
        return column

    @staticmethod
    def save_and_commit(session, column: DatasetTableColumn):
        session.add(column)
        session.commit()

    @staticmethod
    def paginate_active_columns_for_table(session, table_uri: str, filter: dict):
        q = (
            session.query(DatasetTableColumn)
            .filter(
                DatasetTableColumn.tableUri == table_uri,
                DatasetTableColumn.deleted.is_(None),
            )
            .order_by(DatasetTableColumn.columnType.asc())
        )

        if filter.get('filteredColumns'):
            q = q.filter(DatasetTableColumn.name.in_(filter['filteredColumns']))

        if 'term' in filter:
            term = filter['term']
            q = q.filter(
                or_(
                    DatasetTableColumn.label.ilike('%' + term + '%'),
                    DatasetTableColumn.description.ilike('%' + term + '%'),
                )
            ).order_by(DatasetTableColumn.columnType.asc())

        return paginate(query=q, page=filter.get('page', 1), page_size=filter.get('pageSize', 10)).to_dict()
