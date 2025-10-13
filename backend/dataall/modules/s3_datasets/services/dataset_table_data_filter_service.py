import logging
import re
from dataall.base.context import get_context
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.modules.s3_datasets.db.dataset_table_data_filter_repositories import DatasetTableDataFilterRepository
from dataall.modules.s3_datasets.db.dataset_table_repositories import DatasetTableRepository
from dataall.modules.s3_datasets.db.dataset_repositories import DatasetRepository
from dataall.modules.s3_datasets.services.dataset_table_data_filter_enums import DataFilterType
from dataall.modules.s3_datasets.services.dataset_service import DatasetService
from dataall.modules.s3_datasets.services.dataset_permissions import (
    CREATE_TABLE_DATA_FILTER,
    DELETE_TABLE_DATA_FILTER,
    LIST_TABLE_DATA_FILTERS,
    MANAGE_DATASETS,
)
from dataall.base.db import exceptions
from dataall.modules.s3_datasets.aws.lf_data_filter_client import LakeFormationDataFilterClient
from dataall.base.utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)

log = logging.getLogger(__name__)


class DatasetTableDataFilterRequestValidationService:
    @staticmethod
    def _required_param(param, name):
        if not param:
            raise exceptions.RequiredParameter(name)

    @staticmethod
    def validate_data_filter_type(data):
        DatasetTableDataFilterRequestValidationService._required_param(data.get('filterType'), 'filterType')
        if data.get('filterType') not in set(item.value for item in DataFilterType):
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
        NamingConventionService(
            target_label=data.get('filterName'),
            pattern=NamingConventionPattern.DATA_FILTERS,
        ).validate_name()

        DatasetTableDataFilterRequestValidationService.validate_data_filter_type(data)


class DatasetTableDataFilterService:
    @staticmethod
    def _get_table_uri_from_filter(session, uri):
        data_filter = DatasetTableDataFilterRepository.get_data_filter_by_uri(session, filter_uri=uri)
        return data_filter.tableUri

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_DATASETS)
    @ResourcePolicyService.has_resource_permission(CREATE_TABLE_DATA_FILTER)
    def create_table_data_filter(uri: str, data: dict):
        DatasetTableDataFilterRequestValidationService.validate_creation_data_filter_params(uri, data)
        context = get_context()

        with context.db_engine.scoped_session() as session:
            table = DatasetTableRepository.get_dataset_table_by_uri(session, uri)
            dataset = DatasetRepository.get_dataset_by_uri(session, table.datasetUri)
            data_filter = DatasetTableDataFilterRepository.build_data_filter(
                session, context.username, table.tableUri, data
            )

            # Create LF Filter
            lf_client = LakeFormationDataFilterClient(table=table, dataset=dataset)
            lf_client.create_table_row_filter(data_filter) if data.get(
                'filterType'
            ) == DataFilterType.ROW.value else lf_client.create_table_column_filter(data_filter)

            # Save to RDS
            DatasetTableDataFilterRepository.save(session, data_filter=data_filter)
        return data_filter

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_DATASETS)
    @ResourcePolicyService.has_resource_permission(DELETE_TABLE_DATA_FILTER, parent_resource=_get_table_uri_from_filter)
    def delete_table_data_filter(uri: str):
        with get_context().db_engine.scoped_session() as session:
            data_filter = DatasetTableDataFilterRepository.get_data_filter_by_uri(session, filter_uri=uri)

            # Check if Share Items w Filter before Delete
            DatasetService.check_before_delete(session, data_filter.filterUri, action=DELETE_TABLE_DATA_FILTER)

            # Delete LF Filter
            table = DatasetTableRepository.get_dataset_table_by_uri(session, data_filter.tableUri)
            dataset = DatasetRepository.get_dataset_by_uri(session, table.datasetUri)
            lf_client = LakeFormationDataFilterClient(table=table, dataset=dataset)
            lf_client.delete_table_data_filter(data_filter)

            # Delete from RDS
            return DatasetTableDataFilterRepository.delete(session, data_filter)

    @staticmethod
    @ResourcePolicyService.has_resource_permission(LIST_TABLE_DATA_FILTERS)
    def list_table_data_filters(uri: str, data: dict):
        with get_context().db_engine.scoped_session() as session:
            return DatasetTableDataFilterRepository.paginated_data_filters(session, table_uri=uri, data=data)
