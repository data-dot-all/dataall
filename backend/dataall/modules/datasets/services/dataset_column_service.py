from dataall.aws.handlers.service_handlers import Worker
from dataall.aws.handlers.sts import SessionHelper
from dataall.core.context import get_context
from dataall.core.permission_checker import has_resource_permission
from dataall.db import models
from dataall.modules.datasets.aws.glue_table_client import GlueTableClient
from dataall.modules.datasets.db.dataset_column_repository import DatasetColumnRepository
from dataall.modules.datasets.db.dataset_table_repository import DatasetTableRepository
from dataall.modules.datasets.services.dataset_permissions import UPDATE_DATASET_TABLE
from dataall.modules.datasets_base.db.models import DatasetTable, DatasetTableColumn


class DatasetColumnService:

    @staticmethod
    def _get_dataset_uri_for_column(session, column_uri):
        column: DatasetTableColumn = DatasetColumnRepository.get_column(session, column_uri)
        return DatasetColumnService._get_dataset_uri(session, column.tableUri)

    @staticmethod
    def _get_dataset_uri(session, table_uri):
        table = DatasetTableRepository.get_dataset_table_by_uri(session, table_uri)
        return table.datasetUri

    @staticmethod
    def paginate_active_columns_for_table(table_uri: str, filter=None):
        # TODO THERE WAS NO PERMISSION CHECK!!!
        with get_context().db_engine.scoped_session() as session:
            return DatasetColumnRepository.paginate_active_columns_for_table(session, table_uri, filter)

    @classmethod
    @has_resource_permission(UPDATE_DATASET_TABLE, parent_resource=_get_dataset_uri, param_name="table_uri")
    def sync_table_columns(cls, table_uri: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            table: DatasetTable = DatasetTableRepository.get_dataset_table_by_uri(session, table_uri)
            aws = SessionHelper.remote_session(table.AWSAccountId)
            glue_table = GlueTableClient(aws, table).get_table()

            DatasetTableRepository.sync_table_columns(
                session, table, glue_table['Table']
            )
        return cls.paginate_active_columns_for_table(table_uri, {})

    @staticmethod
    @has_resource_permission(UPDATE_DATASET_TABLE, parent_resource=_get_dataset_uri_for_column, param_name="column_uri")
    def update_table_column_description(column_uri: str, description) -> DatasetTableColumn:
        with get_context().db_engine.scoped_session() as session:
            column: DatasetTableColumn = DatasetColumnRepository.get_column(session, column_uri)
            column.description = description

            task = models.Task(
                action='glue.table.update_column', targetUri=column.columnUri
            )
            session.add(task)
            session.commit()

        Worker.queue(engine=get_context().db_engine, task_ids=[task.taskUri])
        return column

