from sqlalchemy import or_

from dataall import db
from dataall.api.context import Context
from dataall.aws.handlers.service_handlers import Worker
from dataall.db import paginate, permissions, models
from dataall.db.api import ResourcePolicy
from dataall.modules.datasets.services.dataset_table import DatasetTableService
from dataall.modules.datasets.db.models import DatasetTableColumn, DatasetTable


def list_table_columns(
    context: Context,
    source: DatasetTable,
    tableUri: str = None,
    filter: dict = None,
):
    if source:
        tableUri = source.tableUri
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        if not source:
            source = DatasetTableService.get_dataset_table_by_uri(session, tableUri)
        q = (
            session.query(DatasetTableColumn)
            .filter(
                DatasetTableColumn.tableUri == tableUri,
                DatasetTableColumn.deleted.is_(None),
            )
            .order_by(DatasetTableColumn.columnType.asc())
        )
        term = filter.get('term')
        if term:
            q = q.filter(
                or_(
                    DatasetTableColumn.label.ilike('%' + term + '%'),
                    DatasetTableColumn.description.ilike('%' + term + '%'),
                )
            ).order_by(DatasetTableColumn.columnType.asc())

    return paginate(
        q, page=filter.get('page', 1), page_size=filter.get('pageSize', 65)
    ).to_dict()


def sync_table_columns(context: Context, source, tableUri: str = None):
    with context.engine.scoped_session() as session:
        table: DatasetTable = DatasetTableService.get_dataset_table_by_uri(
            session, tableUri
        )
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=table.datasetUri,
            permission_name=permissions.UPDATE_DATASET_TABLE,
        )
        task = models.Task(action='glue.table.columns', targetUri=table.tableUri)
        session.add(task)
    Worker.process(engine=context.engine, task_ids=[task.taskUri], save_response=False)
    return list_table_columns(context, source=table, tableUri=tableUri)


def resolve_terms(context, source: DatasetTableColumn, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        q = session.query(models.TermLink).filter(
            models.TermLink.targetUri == source.columnUri
        )
    return paginate(q, page=1, page_size=15).to_dict()


def update_table_column(
    context: Context, source, columnUri: str = None, input: dict = None
):
    with context.engine.scoped_session() as session:
        column: DatasetTableColumn = session.query(
            DatasetTableColumn
        ).get(columnUri)
        if not column:
            raise db.exceptions.ObjectNotFound('Column', columnUri)
        table: DatasetTable = DatasetTableService.get_dataset_table_by_uri(
            session, column.tableUri
        )
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=table.datasetUri,
            permission_name=permissions.UPDATE_DATASET_TABLE,
        )
        column.description = input.get('description', 'No description provided')
        session.add(column)
        session.commit()

        task = models.Task(
            action='glue.table.update_column', targetUri=column.columnUri
        )
        session.add(task)
        session.commit()

    Worker.queue(engine=context.engine, task_ids=[task.taskUri])
    return column
