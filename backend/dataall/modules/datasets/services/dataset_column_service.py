from dataall.core.tasks.service_handlers import Worker
from dataall.base.aws.sts import SessionHelper
from dataall.base.context import get_context
from dataall.core.permissions.permission_checker import has_resource_permission
from dataall.core.tasks.db.task_models import Task
from dataall.core.permissions.db.resource_policy_repositories import ResourcePolicy
from dataall.modules.datasets.aws.glue_table_client import GlueTableClient
from dataall.modules.datasets.db.dataset_column_repositories import DatasetColumnRepository
from dataall.modules.datasets.db.dataset_table_repositories import DatasetTableRepository
from dataall.modules.datasets.services.dataset_permissions import UPDATE_DATASET_TABLE
from dataall.modules.datasets_base.db.dataset_models import DatasetTable, DatasetTableColumn
from dataall.modules.datasets_base.db.dataset_repositories import DatasetRepository
from dataall.modules.datasets_base.services.datasets_base_enums import ConfidentialityClassification
from dataall.modules.datasets_base.services.permissions import PREVIEW_DATASET_TABLE


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
    def paginate_active_columns_for_table(uri: str, filter=None):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            table: DatasetTable = DatasetTableRepository.get_dataset_table_by_uri(session, uri)
            dataset = DatasetRepository.get_dataset_by_uri(session, table.datasetUri)
            if (
                ConfidentialityClassification.get_confidentiality_level(dataset.confidentiality)
                != ConfidentialityClassification.Unclassified.value
            ):
                ResourcePolicy.check_user_resource_permission(
                    session=session,
                    username=context.username,
                    groups=context.groups,
                    resource_uri=table.tableUri,
                    permission_name=PREVIEW_DATASET_TABLE,
                )
            return DatasetColumnRepository.paginate_active_columns_for_table(session, uri, filter)

    @classmethod
    @has_resource_permission(UPDATE_DATASET_TABLE, parent_resource=_get_dataset_uri, param_name='table_uri')
    def sync_table_columns(cls, table_uri: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            table: DatasetTable = DatasetTableRepository.get_dataset_table_by_uri(session, table_uri)
            aws = SessionHelper.remote_session(table.AWSAccountId, table.region)
            glue_table = GlueTableClient(aws, table).get_table()

            DatasetTableRepository.sync_table_columns(session, table, glue_table['Table'])
        return cls.paginate_active_columns_for_table(uri=table_uri, filter={})

    @staticmethod
    @has_resource_permission(UPDATE_DATASET_TABLE, parent_resource=_get_dataset_uri_for_column, param_name='column_uri')
    def update_table_column_description(column_uri: str, description) -> DatasetTableColumn:
        with get_context().db_engine.scoped_session() as session:
            column: DatasetTableColumn = DatasetColumnRepository.get_column(session, column_uri)
            column.description = description

            task = Task(action='glue.table.update_column', targetUri=column.columnUri)
            session.add(task)
            session.commit()

        Worker.queue(engine=get_context().db_engine, task_ids=[task.taskUri])
        return column
