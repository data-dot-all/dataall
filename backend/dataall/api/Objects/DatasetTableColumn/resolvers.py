from sqlalchemy import or_

from .... import db
from ....api.context import Context
from ....aws.handlers.service_handlers import Worker
from ....db import paginate, permissions, models
from ....db.api import ResourcePolicy
import time

def list_table_columns(
    context: Context,
    source: models.DatasetTable,
    tableUri: str = None,
    filter: dict = None,
):
    if source:
        tableUri = source.tableUri
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        if not source:
            source = db.api.DatasetTable.get_dataset_table_by_uri(session, tableUri)
        q = (
            session.query(models.DatasetTableColumn)
            .filter(
                models.DatasetTableColumn.tableUri == tableUri,
                models.DatasetTableColumn.deleted.is_(None),
            )
            .order_by(models.DatasetTableColumn.columnType.asc())
        )
        term = filter.get('term')
        if term:
            q = q.filter(
                or_(
                    models.DatasetTableColumn.label.ilike('%' + term + '%'),
                    models.DatasetTableColumn.description.ilike('%' + term + '%'),
                )
            ).order_by(models.DatasetTableColumn.columnType.asc())

    return paginate(
        q, page=filter.get('page', 1), page_size=filter.get('pageSize', 65)
    ).to_dict()


def sync_table_columns(context: Context, source, tableUri: str = None):
    with context.engine.scoped_session() as session:
        table: models.DatasetTable = db.api.DatasetTable.get_dataset_table_by_uri(
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
    time.sleep(5)
    return list_table_columns(context, source=table, tableUri=tableUri)


def resolve_terms(context, source: models.DatasetTableColumn, **kwargs):
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
        column: models.DatasetTableColumn = session.query(
            models.DatasetTableColumn
        ).get(columnUri)
        if not column:
            raise db.exceptions.ObjectNotFound('Column', columnUri)
        table: models.DatasetTable = db.api.DatasetTable.get_dataset_table_by_uri(
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


def update_table_column_lf_tags(
    context: Context, source, columnUri: str = None, input: dict = None
):
    with context.engine.scoped_session() as session:
        column: models.DatasetTableColumn = session.query(
            models.DatasetTableColumn
        ).get(columnUri)
        if not column:
            raise db.exceptions.ObjectNotFound('Column', columnUri)
        table: models.DatasetTable = db.api.DatasetTable.get_dataset_table_by_uri(
            session, column.tableUri
        )
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=table.datasetUri,
            permission_name=permissions.UPDATE_DATASET_TABLE,
        )
        
        column.lfTagKey = input.get("lfTagKey", [])
        column.lfTagValue = input.get("lfTagValue", [])
        session.add(column)
        session.commit()

        task = models.Task(
            action='lakeformation.column.assign.lftags', targetUri=column.columnUri
        )
        session.add(task)
        session.commit()

    Worker.queue(engine=context.engine, task_ids=[task.taskUri])
    return column