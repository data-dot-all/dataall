from operator import or_

from dataall.db import paginate
from dataall.db.exceptions import ObjectNotFound
from dataall.modules.datasets_base.db.models import DatasetTableColumn


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
    def paginate_active_columns_for_table(session, table_uri: str, term, page, page_size):
        q = (
            session.query(DatasetTableColumn)
            .filter(
                DatasetTableColumn.tableUri == table_uri,
                DatasetTableColumn.deleted.is_(None),
            )
            .order_by(DatasetTableColumn.columnType.asc())
        )

        if term:
            q = q.filter(
                or_(
                    DatasetTableColumn.label.ilike('%' + term + '%'),
                    DatasetTableColumn.description.ilike('%' + term + '%'),
                )
            ).order_by(DatasetTableColumn.columnType.asc())

        return paginate(q, page=page, page_size=page_size).to_dict()


