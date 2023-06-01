from dataall.aws.handlers.service_handlers import Worker
from dataall.core.context import get_context
from dataall.db import models
from dataall.db.api import ResourcePolicy
from dataall.modules.datasets.db.dataset_column_repository import DatasetColumnRepository
from dataall.modules.datasets.db.dataset_table_repository import DatasetTableRepository
from dataall.modules.datasets.services.dataset_permissions import UPDATE_DATASET_TABLE
from dataall.modules.datasets_base.db.models import DatasetTable, DatasetTableColumn


class DatasetColumnService:

    @staticmethod
    def paginate_active_columns_for_table(table_uri: str, filter=None):
        # TODO THERE WAS NO PERMISSION CHECK!!!
        with get_context().db_engine.scoped_session() as session:
            return DatasetColumnRepository.paginate_active_columns_for_table(session, table_uri, filter)

    @staticmethod
    def sync_table_columns(table_uri: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            DatasetColumnService._check_resource_permission(session, table_uri, UPDATE_DATASET_TABLE)
            task = models.Task(action='glue.table.columns', targetUri=table_uri)
            session.add(task)
        Worker.process(engine=context.db_engine, task_ids=[task.taskUri], save_response=False)
        return DatasetColumnService.paginate_active_columns_for_table(table_uri)

    @staticmethod
    def update_table_column_description(column_uri: str, description) -> DatasetTableColumn:
        with get_context().db_engine.scoped_session() as session:
            column: DatasetTableColumn = DatasetColumnRepository.get_column(session, column_uri)
            DatasetColumnService._check_resource_permission(session, column.tableUri, UPDATE_DATASET_TABLE)

            column.description = description

            task = models.Task(
                action='glue.table.update_column', targetUri=column.columnUri
            )
            session.add(task)
            session.commit()

        Worker.queue(engine=get_context().db_engine, task_ids=[task.taskUri])
        return column

    @staticmethod
    def _check_resource_permission(session, table_uri: str, permission):
        context = get_context()
        table: DatasetTable = DatasetTableRepository.get_dataset_table_by_uri(session, table_uri)
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=table.datasetUri,
            permission_name=permission,
        )
