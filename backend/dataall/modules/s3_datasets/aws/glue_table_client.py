import logging

from botocore.exceptions import ClientError

from dataall.modules.s3_datasets.db.dataset_models import DatasetTable

log = logging.getLogger(__name__)


class GlueTableClient:
    """Makes requests to AWS Glue API"""

    def __init__(self, aws_session, table: DatasetTable):
        self._client = aws_session.client('glue', region_name=table.region)
        self._table = table

    def get_table(self):
        dataset_table = self._table
        try:
            glue_table = self._client.get_table(
                CatalogId=dataset_table.AWSAccountId,
                DatabaseName=dataset_table.GlueDatabaseName,
                Name=dataset_table.name,
            )
            return glue_table
        except ClientError as e:
            log.error(
                f'Failed to get table aws://{dataset_table.AWSAccountId}'
                f'//{dataset_table.GlueDatabaseName}'
                f'//{dataset_table.name} due to: '
                f'{e}'
            )
            return {}

    def update_table_for_column(self, column_name, table_input):
        try:
            response = self._client.update_table(
                DatabaseName=self._table.GlueDatabaseName,
                TableInput=table_input,
            )
            log.info(f'Column {column_name} updated successfully: {response}')
        except ClientError as e:
            log.error(f'Failed to update table column {column_name} description: {e}')
            raise e
