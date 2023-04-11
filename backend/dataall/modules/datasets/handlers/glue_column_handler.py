import logging

from botocore.exceptions import ClientError

from dataall.aws.handlers.sts import SessionHelper
from dataall.db import models
from dataall.aws.handlers.service_handlers import Worker
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
            glue_client = aws.client('glue', region_name=dataset_table.region)
            glue_table = {}
            try:
                glue_table = glue_client.get_table(
                    CatalogId=dataset_table.AWSAccountId,
                    DatabaseName=dataset_table.GlueDatabaseName,
                    Name=dataset_table.name,
                )
            except glue_client.exceptions.ClientError as e:
                log.error(
                    f'Failed to get table aws://{dataset_table.AWSAccountId}'
                    f'//{dataset_table.GlueDatabaseName}'
                    f'//{dataset_table.name} due to: '
                    f'{e}'
                )
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
            try:
                aws_session = SessionHelper.remote_session(table.AWSAccountId)

                DatasetColumnGlueHandler.grant_pivot_role_all_table_permissions(aws_session, table)

                glue_client = aws_session.client('glue', region_name=table.region)

                original_table = glue_client.get_table(
                    CatalogId=table.AWSAccountId,
                    DatabaseName=table.GlueDatabaseName,
                    Name=table.name,
                )
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
                all_columns = updated_table.get('StorageDescriptor', {}).get(
                    'Columns', []
                ) + updated_table.get('PartitionKeys', [])
                for col in all_columns:
                    if col['Name'] == column.name:
                        col['Comment'] = column.description
                        log.info(
                            f'Found column {column.name} adding description {column.description}'
                        )
                        response = glue_client.update_table(
                            DatabaseName=table.GlueDatabaseName,
                            TableInput=updated_table,
                        )
                        log.info(
                            f'Column {column.name} updated successfully: {response}'
                        )
                return True

            except ClientError as e:
                log.error(
                    f'Failed to update table column {column.name} description: {e}'
                )
                raise e

    @staticmethod
    def grant_pivot_role_all_table_permissions(aws_session, table):
        """
        Pivot role needs to have all permissions
        for tables managed inside dataall
        :param aws_session:
        :param table:
        :return:
        """
        try:
            lf_client = aws_session.client('lakeformation', region_name=table.region)
            grant_dict = dict(
                Principal={
                    'DataLakePrincipalIdentifier': SessionHelper.get_delegation_role_arn(
                        table.AWSAccountId
                    )
                },
                Resource={
                    'Table': {
                        'DatabaseName': table.GlueDatabaseName,
                        'Name': table.name,
                    }
                },
                Permissions=['SELECT', 'ALTER', 'DROP', 'INSERT'],
            )
            response = lf_client.grant_permissions(**grant_dict)
            log.error(
                f'Successfully granted pivot role all table '
                f'aws://{table.AWSAccountId}/{table.GlueDatabaseName}/{table.name} '
                f'access: {response}'
            )
        except ClientError as e:
            log.error(
                f'Failed to grant pivot role all table '
                f'aws://{table.AWSAccountId}/{table.GlueDatabaseName}/{table.name} '
                f'access: {e}'
            )
            raise e
