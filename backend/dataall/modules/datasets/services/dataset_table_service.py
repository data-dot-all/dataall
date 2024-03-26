import logging

from dataall.base.context import get_context
from dataall.modules.catalog.db.glossary_repositories import GlossaryRepository
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.permissions.db.resource_policy_repositories import ResourcePolicy
from dataall.core.permissions.permission_checker import has_resource_permission, has_tenant_permission
from dataall.base.db.exceptions import ResourceShared
from dataall.modules.dataset_sharing.db.share_object_repositories import ShareObjectRepository
from dataall.modules.datasets.aws.athena_table_client import AthenaTableClient
from dataall.modules.datasets.aws.glue_dataset_client import DatasetCrawler
from dataall.modules.datasets.db.dataset_table_repositories import DatasetTableRepository
from dataall.modules.datasets.indexers.table_indexer import DatasetTableIndexer
from dataall.modules.datasets.services.dataset_permissions import (
    UPDATE_DATASET_TABLE,
    MANAGE_DATASETS,
    DELETE_DATASET_TABLE,
    SYNC_DATASET,
)
from dataall.modules.datasets_base.db.dataset_repositories import DatasetRepository
from dataall.modules.datasets_base.services.datasets_base_enums import ConfidentialityClassification
from dataall.modules.datasets_base.db.dataset_models import DatasetTable, Dataset
from dataall.modules.datasets_base.services.permissions import (
    PREVIEW_DATASET_TABLE,
    DATASET_TABLE_READ,
    GET_DATASET_TABLE,
)
from dataall.base.utils import json_utils

log = logging.getLogger(__name__)


class DatasetTableService:
    @staticmethod
    def _get_dataset_uri(session, table_uri):
        table = DatasetTableRepository.get_dataset_table_by_uri(session, table_uri)
        return table.datasetUri

    @staticmethod
    @has_tenant_permission(MANAGE_DATASETS)
    def get_table(uri: str):
        with get_context().db_engine.scoped_session() as session:
            return DatasetTableRepository.get_dataset_table_by_uri(session, uri)

    @staticmethod
    @has_tenant_permission(MANAGE_DATASETS)
    @has_resource_permission(UPDATE_DATASET_TABLE, parent_resource=_get_dataset_uri)
    def update_table(uri: str, table_data: dict = None):
        with get_context().db_engine.scoped_session() as session:
            table = DatasetTableRepository.get_dataset_table_by_uri(session, uri)

            for k in [attr for attr in table_data.keys() if attr != 'terms']:
                setattr(table, k, table_data.get(k))

            DatasetTableRepository.save(session, table)
            if 'terms' in table_data:
                GlossaryRepository.set_glossary_terms_links(
                    session, get_context().username, table.tableUri, 'DatasetTable', table_data['terms']
                )

        DatasetTableIndexer.upsert(session, table_uri=table.tableUri)
        return table

    @staticmethod
    @has_tenant_permission(MANAGE_DATASETS)
    @has_resource_permission(DELETE_DATASET_TABLE, parent_resource=_get_dataset_uri)
    def delete_table(uri: str):
        with get_context().db_engine.scoped_session() as session:
            table = DatasetTableRepository.get_dataset_table_by_uri(session, uri)
            has_share = ShareObjectRepository.has_shared_items(session, table.tableUri)
            if has_share:
                raise ResourceShared(
                    action=DELETE_DATASET_TABLE,
                    message='Revoke all table shares before deletion',
                )

            ShareObjectRepository.delete_shares(session, table.tableUri)
            DatasetTableRepository.delete(session, table)

            GlossaryRepository.delete_glossary_terms_links(
                session, target_uri=table.tableUri, target_type='DatasetTable'
            )
        DatasetTableIndexer.delete_doc(doc_id=uri)
        return True

    @staticmethod
    def preview(table_uri: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            table: DatasetTable = DatasetTableRepository.get_dataset_table_by_uri(session, table_uri)
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
            env = EnvironmentService.get_environment_by_uri(session, dataset.environmentUri)
            return AthenaTableClient(env, table).get_table(dataset_uri=dataset.datasetUri)

    @staticmethod
    @has_resource_permission(GET_DATASET_TABLE)
    def get_glue_table_properties(uri: str):
        with get_context().db_engine.scoped_session() as session:
            table: DatasetTable = DatasetTableRepository.get_dataset_table_by_uri(session, uri)
            return json_utils.to_string(table.GlueTableProperties).replace('\\', ' ')

    @staticmethod
    def list_shared_tables_by_env_dataset(dataset_uri: str, env_uri: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            return [
                {'tableUri': t.tableUri, 'GlueTableName': t.GlueTableName}
                for t in DatasetTableRepository.query_dataset_tables_shared_with_env(
                    session, env_uri, dataset_uri, context.username, context.groups
                )
            ]

    @classmethod
    @has_resource_permission(SYNC_DATASET)
    def sync_tables_for_dataset(cls, uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            dataset = DatasetRepository.get_dataset_by_uri(session, uri)
            S3Prefix = dataset.S3BucketName
            tables = DatasetCrawler(dataset).list_glue_database_tables(S3Prefix)
            cls.sync_existing_tables(session, dataset.datasetUri, glue_tables=tables)
            DatasetTableIndexer.upsert_all(session=session, dataset_uri=dataset.datasetUri)
            DatasetTableIndexer.remove_all_deleted(session=session, dataset_uri=dataset.datasetUri)
            return DatasetRepository.paginated_dataset_tables(
                session=session,
                uri=uri,
                data={'page': 1, 'pageSize': 10},
            )

    @staticmethod
    def sync_existing_tables(session, dataset_uri, glue_tables=None):
        dataset: Dataset = DatasetRepository.get_dataset_by_uri(session, dataset_uri)
        if dataset:
            existing_tables = DatasetTableRepository.find_dataset_tables(session, dataset_uri)
            existing_table_names = [e.GlueTableName for e in existing_tables]
            existing_dataset_tables_map = {t.GlueTableName: t for t in existing_tables}

            DatasetTableRepository.update_existing_tables_status(existing_tables, glue_tables)
            log.info(f'existing_tables={glue_tables}')
            for table in glue_tables:
                if table['Name'] not in existing_table_names:
                    log.info(f'Storing new table: {table} for dataset db {dataset.GlueDatabaseName}')
                    updated_table = DatasetTableRepository.create_synced_table(session, dataset, table)
                    DatasetTableService._attach_dataset_table_permission(session, dataset, updated_table.tableUri)
                else:
                    log.info(f'Updating table: {table} for dataset db {dataset.GlueDatabaseName}')
                    updated_table: DatasetTable = existing_dataset_tables_map.get(table['Name'])
                    updated_table.GlueTableProperties = json_utils.to_json(table.get('Parameters', {}))

                DatasetTableRepository.sync_table_columns(session, updated_table, table)

        return True

    @staticmethod
    def _attach_dataset_table_permission(session, dataset: Dataset, table_uri):
        # ADD DATASET TABLE PERMISSIONS
        env = EnvironmentService.get_environment_by_uri(session, dataset.environmentUri)
        permission_group = {
            dataset.SamlAdminGroupName,
            env.SamlGroupName,
            dataset.stewards if dataset.stewards is not None else dataset.SamlAdminGroupName,
        }
        for group in permission_group:
            ResourcePolicy.attach_resource_policy(
                session=session,
                group=group,
                permissions=DATASET_TABLE_READ,
                resource_uri=table_uri,
                resource_type=DatasetTable.__name__,
            )
