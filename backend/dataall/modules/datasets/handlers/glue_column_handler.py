import logging

from dataall.aws.handlers.sts import SessionHelper
from dataall.db import models
from dataall.aws.handlers.service_handlers import Worker
from dataall.modules.datasets.aws.glue_table_client import GlueTableClient
from dataall.modules.datasets.aws.lf_table_client import LakeFormationTableClient
from dataall.modules.datasets.db.table_column_model import DatasetTableColumn
from dataall.modules.datasets.services.dataset_table import DatasetTableService

log = logging.getLogger(__name__)


class DatasetColumnGlueHandler:
    """A handler for dataset table columns"""

    @staticmethod
    @Worker.handler('glue.table.columns')
    def get_table_columns(engine, task: models.Task):
        with engine.scoped_session() as session:
            dataset_table: models.DatasetTable = session.query(models.DatasetTable).get(
                task.targetUri
            )
            aws = SessionHelper.remote_session(dataset_table.AWSAccountId)
            glue_table = GlueTableClient(aws, dataset_table).get_table()

            DatasetTableService.sync_table_columns(
                session, dataset_table, glue_table['Table']
            )
        return True

    @staticmethod
    @Worker.handler('glue.table.update_column')
    def update_table_columns(engine, task: models.Task):
        with engine.scoped_session() as session:
            column: DatasetTableColumn = session.query(
                DatasetTableColumn
            ).get(task.targetUri)
            table: models.DatasetTable = session.query(models.DatasetTable).get(
                column.tableUri
            )

            aws_session = SessionHelper.remote_session(table.AWSAccountId)

            LakeFormationTableClient(aws_session, table).grant_pivot_role_all_table_permissions()
            glue_client = GlueTableClient(aws_session, table)
            original_table = glue_client.get_table()
            updated_table = {
                k: v
                for k, v in original_table['Table'].items()
                if k not in [
                    'CatalogId',
                    'VersionId',
                    'DatabaseName',
                    'CreateTime',
                    'UpdateTime',
                    'CreatedBy',
                    'IsRegisteredWithLakeFormation',
                ]
            }
            all_columns = updated_table.get('StorageDescriptor', {}).get(
                'Columns', []
            ) + updated_table.get('PartitionKeys', [])
            for col in all_columns:
                if col['Name'] == column.name:
                    col['Comment'] = column.description
                    log.info(
                        f'Found column {column.name} adding description {column.description}'
                    )

                    glue_client.update_table_for_column(column.name, updated_table)

