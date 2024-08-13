import logging
from botocore.exceptions import ClientError

from dataall.base.aws.sts import SessionHelper
from dataall.modules.s3_datasets.db.dataset_models import DatasetTable, DatasetTableDataFilter, S3Dataset

log = logging.getLogger(__name__)


class LakeFormationDataFilterClient:
    """Requests to AWS LakeFormation"""

    def __init__(self, table: DatasetTable, dataset: S3Dataset, aws_session=None):
        if not aws_session:
            base_session = SessionHelper.remote_session(table.AWSAccountId, table.region)
            aws_session = SessionHelper.get_session(base_session=base_session, role_arn=dataset.IAMDatasetAdminRoleArn)

        self._client = aws_session.client('lakeformation', region_name=table.region)
        self._table = table

    def delete_table_data_filter(self, data_filter: DatasetTableDataFilter):
        try:
            self._client.delete_data_cells_filter(
                TableCatalogId=self._table.AWSAccountId,
                DatabaseName=self._table.GlueDatabaseName,
                TableName=self._table.name,
                Name=data_filter.label,
            )
        except self._client.exceptions.EntityNotFoundException:
            log.info(f'Data filter {data_filter.label} not found, passing...')

    def create_table_row_filter(self, data_filter: DatasetTableDataFilter):
        RowFilter = {
            'RowFilter': {
                'FilterExpression': data_filter.rowExpression,
            },
            'ColumnWildcard': {'ExcludedColumnNames': []},
        }
        self._create_table_data_filter(data_filter, RowFilter)

    def create_table_column_filter(self, data_filter: DatasetTableDataFilter):
        ColumnFilter = {'ColumnNames': data_filter.includedCols, 'RowFilter': {'AllRowsWildcard': {}}}
        self._create_table_data_filter(data_filter, ColumnFilter)

    def _create_table_data_filter(self, data_filter: DatasetTableDataFilter, filterExpression):
        return self._client.create_data_cells_filter(
            TableData={
                'TableCatalogId': self._table.AWSAccountId,
                'DatabaseName': self._table.GlueDatabaseName,
                'TableName': self._table.name,
                'Name': data_filter.label,
                **filterExpression,
            }
        )
