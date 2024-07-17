import logging

from dataall.base.context import get_context
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.modules.catalog.db.glossary_repositories import GlossaryRepository
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.modules.s3_datasets.aws.athena_table_client import AthenaTableClient
from dataall.modules.s3_datasets.aws.glue_dataset_client import DatasetCrawler
from dataall.modules.s3_datasets.db.dataset_table_repositories import DatasetTableRepository
from dataall.modules.s3_datasets.indexers.table_indexer import DatasetTableIndexer
from dataall.modules.s3_datasets.indexers.dataset_indexer import DatasetIndexer
from dataall.modules.s3_datasets.services.dataset_permissions import (
    UPDATE_DATASET_TABLE,
    MANAGE_DATASETS,
    DELETE_DATASET_TABLE,
    SYNC_DATASET,
)
from dataall.modules.s3_datasets.db.dataset_table_data_filter_repositories import DatasetTableDataFilterRepository
from dataall.modules.s3_datasets.services.dataset_table_data_filter_enums import DataFilterType
from dataall.modules.s3_datasets.db.dataset_models import DatasetTableDataFilter, S3Dataset
from dataall.modules.s3_datasets.services.dataset_permissions import (
    PREVIEW_DATASET_TABLE,
    DATASET_TABLE_READ,
    GET_DATASET_TABLE,
    CREATE_TABLE_DATA_FILTER,
    DELETE_TABLE_DATA_FILTER,
    LIST_TABLE_DATA_FILTERS,
)
from dataall.modules.s3_datasets.services.dataset_service import DatasetService
from dataall.base.utils import json_utils
from dataall.base.db import exceptions

log = logging.getLogger(__name__)


class DatasetTableDataFilterRequestValidationService:
    @staticmethod
    def _required_param(param, name):
        if not param:
            raise exceptions.RequiredParameter(name)

    @staticmethod
    def validate_data_filter_type(data):
        DatasetTableDataFilterRequestValidationService._required_param(data.get('filterType'), 'filterType')
        if data.get('filterType') not in DataFilterType:
            raise exceptions.InvalidInput(
                'filterType',
                data.get('filterType'),
                'ROW or COLUMN value',
            )
        if data.get('filterType') == DataFilterType.ROW.value and not data.get('rowExpression'):
            raise exceptions.InvalidInput(
                'rowExpression',
                data.get('rowExpression'),
                f'must be provided for {data.get("filterType")} filter',
            )
        if data.get('filterType') == DataFilterType.COLUMN.value and not data.get('includedCols'):
            raise exceptions.InvalidInput(
                'includedCols',
                data.get('includedCols'),
                f'must be provided for {data.get("filterType")} filter',
            )

    @staticmethod
    def validate_creation_data_filter_params(uri, data):
        DatasetTableDataFilterRequestValidationService._required_param(uri, 'tableUri')
        DatasetTableDataFilterRequestValidationService._required_param(data, 'data')
        DatasetTableDataFilterRequestValidationService._required_param(data.get('filterName'), 'filterName')
        DatasetTableDataFilterRequestValidationService.validate_data_filter_type(data)


class DatasetTableDataFilterService:
    @staticmethod
    @ResourcePolicyService.has_resource_permission(CREATE_TABLE_DATA_FILTER)
    def create_table_data_filter(uri: str, data: dict):
        DatasetTableDataFilterRequestValidationService.validate_creation_data_filter_params(uri, data)
        context = get_context()

        with context.db_engine.scoped_session() as session:
            data_filter = DatasetTableDataFilter(
                tableUri=uri,
                label=data.get('filterName'),
                filterType=data.get('filterType'),
                rowExpression=data.get('rowExpression') if data.get('filterType') == DataFilterType.ROW.value else None,
                includedCols=data.get('includedCols')
                if data.get('filterType') == DataFilterType.COLUMN.value
                else None,
                owner=context.username,
            )

            DatasetTableDataFilterRepository.save(session, data_filter=data_filter)
        return data_filter

    @staticmethod
    @ResourcePolicyService.has_resource_permission(DELETE_TABLE_DATA_FILTER)
    def delete_table_data_filter(uri: str):
        with get_context().db_engine.scoped_session() as session:
            data_filter = DatasetTableDataFilterRepository.find_by_uri(session, uri=uri)
            return DatasetTableDataFilterRepository.delete_table_data_filter(session, data_filter)

    @staticmethod
    @ResourcePolicyService.has_resource_permission(LIST_TABLE_DATA_FILTERS)
    def list_table_data_filters(uri: str, data: dict):
        return DatasetTableDataFilterRepository.paginated_data_filters(table_uri=uri, data=data)
