import logging

from dataall.core.tasks.service_handlers import Worker
from dataall.base.aws.sts import SessionHelper
from dataall.core.tasks.db.task_models import Task
from dataall.modules.s3_datasets.aws.glue_table_client import GlueTableClient
from dataall.modules.s3_datasets.aws.lf_table_client import LakeFormationTableClient
from dataall.modules.s3_datasets.db.dataset_models import DatasetTableColumn, DatasetTable

log = logging.getLogger(__name__)


class DatasetColumnGlueHandler:
    """A handler for dataset table columns"""

    @staticmethod
    @Worker.handler('glue.table.update_column')
    def update_table_columns(engine, task: Task):
        with engine.scoped_session() as session:
            column: DatasetTableColumn = session.query(DatasetTableColumn).get(task.targetUri)
            table: DatasetTable = session.query(DatasetTable).get(column.tableUri)

            aws_session = SessionHelper.remote_session(table.AWSAccountId, table.region)

            lf_client = LakeFormationTableClient(table=table, aws_session=aws_session)
            lf_client.grant_pivot_role_all_table_permissions()

            glue_client = GlueTableClient(aws_session=aws_session, table=table)
            original_table = glue_client.get_table()
            updated_table = {
                k: v
                for k, v in original_table['Table'].items()
                if k
                not in [
                    'CatalogId',
                    'VersionId',
                    'DatabaseName',
                    'CreateTime',
                    'UpdateTime',
                    'CreatedBy',
                    'IsRegisteredWithLakeFormation',
                ]
            }
            all_columns = updated_table.get('StorageDescriptor', {}).get('Columns', []) + updated_table.get(
                'PartitionKeys', []
            )
            for col in all_columns:
                if col['Name'] == column.name:
                    col['Comment'] = column.description
                    log.info(f'Found column {column.name} adding description {column.description}')

                    glue_client.update_table_for_column(column.name, updated_table)
