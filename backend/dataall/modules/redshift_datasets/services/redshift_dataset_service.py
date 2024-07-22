import logging

from dataall.base.context import get_context
from dataall.base.db.paginator import paginate_list
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.core.permissions.services.group_policy_service import GroupPolicyService
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.modules.vote.db.vote_repositories import VoteRepository
from dataall.modules.catalog.db.glossary_repositories import GlossaryRepository


from dataall.modules.datasets_base.services.datasets_enums import DatasetRole
from dataall.modules.datasets_base.db.dataset_repositories import DatasetBaseRepository

from dataall.modules.redshift_datasets.services.redshift_dataset_permissions import (
    MANAGE_REDSHIFT_DATASETS,
    IMPORT_REDSHIFT_DATASET,
    ADD_TABLES_REDSHIFT_DATASET,
    DELETE_REDSHIFT_DATASET,
    UPDATE_REDSHIFT_DATASET,
    GET_REDSHIFT_DATASET,
    REDSHIFT_DATASET_ALL,
    REDSHIFT_DATASET_READ,
    GET_REDSHIFT_DATASET_TABLE,
    DELETE_REDSHIFT_DATASET_TABLE,
    REDSHIFT_DATASET_TABLE_ALL,
    REDSHIFT_DATASET_TABLE_READ,
)
from dataall.modules.redshift_datasets.db.redshift_dataset_repositories import RedshiftDatasetRepository
from dataall.modules.redshift_datasets.db.redshift_connection_repositories import RedshiftConnectionRepository
from dataall.modules.redshift_datasets.db.redshift_models import RedshiftDataset, RedshiftTable
from dataall.modules.redshift_datasets.aws.redshift_data import RedshiftData
from dataall.modules.redshift_datasets.indexers.dataset_indexer import DatasetIndexer
from dataall.modules.redshift_datasets.indexers.table_indexer import DatasetTableIndexer


log = logging.getLogger(__name__)


class RedshiftDatasetService:
    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_REDSHIFT_DATASETS)
    @ResourcePolicyService.has_resource_permission(IMPORT_REDSHIFT_DATASET)
    @GroupPolicyService.has_group_permission(IMPORT_REDSHIFT_DATASET)
    def import_redshift_dataset(uri, admin_group, data: dict):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            environment = EnvironmentService.get_environment_by_uri(session, uri)

            dataset = RedshiftDatasetRepository.create_redshift_dataset(
                session=session, username=context.username, env=environment, data=data
            )
            dataset.userRoleForDataset = DatasetRole.Creator.value

            RedshiftDatasetService._attach_dataset_permissions(session, dataset, environment)

            DatasetIndexer.upsert(session=session, dataset_uri=dataset.datasetUri)

            for table in data.get('tables', []):
                rs_table = RedshiftDatasetRepository.create_redshift_table(
                    session=session,
                    username=context.username,
                    dataset_uri=dataset.datasetUri,
                    data={'name': table},
                )
                RedshiftDatasetService._attach_table_permissions(session, dataset, environment, rs_table)
                DatasetTableIndexer.upsert(session=session, table_uri=rs_table.rsTableUri)

        return dataset

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_REDSHIFT_DATASETS)
    @ResourcePolicyService.has_resource_permission(UPDATE_REDSHIFT_DATASET)
    def update_redshift_dataset(uri, data: dict):
        context = get_context()
        username = context.username
        with context.db_engine.scoped_session() as session:
            dataset: RedshiftDataset = RedshiftDatasetRepository.get_redshift_dataset_by_uri(session, uri)
            if data and isinstance(data, dict):
                for k in data.keys():
                    if k not in ['stewards']:
                        setattr(dataset, k, data.get(k))

                if data.get('stewards') and data.get('stewards') != dataset.stewards:
                    if data.get('stewards') != dataset.SamlAdminGroupName:
                        RedshiftDatasetService._transfer_stewardship_to_new_stewards(session, dataset, data['stewards'])
                        dataset.stewards = data['stewards']
                    else:
                        RedshiftDatasetService._transfer_stewardship_to_owners(session, dataset)
                        dataset.stewards = dataset.SamlAdminGroupName

                ResourcePolicyService.attach_resource_policy(
                    session=session,
                    group=dataset.SamlAdminGroupName,
                    permissions=REDSHIFT_DATASET_ALL,
                    resource_uri=dataset.datasetUri,
                    resource_type=RedshiftDataset.__name__,
                )
                if data.get('terms'):
                    GlossaryRepository.set_glossary_terms_links(
                        session, username, uri, 'RedshiftDataset', data.get('terms')
                    )
                    for table in RedshiftDatasetRepository.list_redshift_dataset_tables(session, dataset.datasetUri):
                        GlossaryRepository.set_glossary_terms_links(
                            session, username, table.rsTableUri, 'RedshiftDatasetTable', data.get('terms')
                        )
                DatasetBaseRepository.update_dataset_activity(session, dataset, username)

            DatasetIndexer.upsert(session, dataset_uri=uri)
            return dataset

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_REDSHIFT_DATASETS)
    @ResourcePolicyService.has_resource_permission(DELETE_REDSHIFT_DATASET)
    def delete_redshift_dataset(uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            dataset: RedshiftDataset = RedshiftDatasetRepository.get_redshift_dataset_by_uri(session, uri)

            # TODO: when adding sharing, add check_on_delete for shared items
            tables: [RedshiftTable] = RedshiftDatasetRepository.list_redshift_dataset_tables(
                session, dataset.datasetUri
            )
            for table in tables:
                DatasetTableIndexer.delete_doc(doc_id=table.rsTableUri)
                session.delete(table)

            ResourcePolicyService.delete_resource_policy(
                session=session, resource_uri=uri, group=dataset.SamlAdminGroupName
            )
            env = EnvironmentService.get_environment_by_uri(session, dataset.environmentUri)
            if dataset.SamlAdminGroupName != env.SamlGroupName:
                ResourcePolicyService.delete_resource_policy(session=session, resource_uri=uri, group=env.SamlGroupName)
            if dataset.stewards:
                ResourcePolicyService.delete_resource_policy(session=session, resource_uri=uri, group=dataset.stewards)

            DatasetTableIndexer.delete_doc(doc_id=dataset.datasetUri)
            # TODO: DatasetService.delete_dataset_term_links(session, uri)
            # todo: VoteRepository.delete_votes(session, dataset.datasetUri, 'dataset')
            session.delete(dataset)
            session.commit()
            return True

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_REDSHIFT_DATASETS)
    @ResourcePolicyService.has_resource_permission(ADD_TABLES_REDSHIFT_DATASET)
    def add_redshift_dataset_tables(uri, tables):
        context = get_context()
        datasetUri = uri
        with context.db_engine.scoped_session() as session:
            dataset = RedshiftDatasetRepository.get_redshift_dataset_by_uri(session, datasetUri)
            dataset_tables = RedshiftDatasetRepository.list_redshift_dataset_tables(session, datasetUri)
            tables = [new_t for new_t in tables if new_t not in [t.name for t in dataset_tables]]
            for table in tables:
                rs_table = RedshiftDatasetRepository.create_redshift_table(
                    session=session,
                    username=context.username,
                    dataset_uri=datasetUri,
                    data={'name': table},
                )
                ResourcePolicyService.attach_resource_policy(
                    session=session,
                    group=dataset.SamlAdminGroupName,
                    permissions=REDSHIFT_DATASET_TABLE_ALL,
                    resource_uri=rs_table.rsTableUri,
                    resource_type=RedshiftTable.__name__,
                )
                DatasetTableIndexer.upsert(session=session, table_uri=rs_table.rsTableUri)
        return True

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_REDSHIFT_DATASETS)
    @ResourcePolicyService.has_resource_permission(DELETE_REDSHIFT_DATASET_TABLE)
    def delete_redshift_dataset_table(uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            table: RedshiftTable = RedshiftDatasetRepository.get_redshift_table_by_uri(session, uri)
            DatasetTableIndexer.delete_doc(doc_id=table.rsTableUri)
            session.delete(table)
            session.commit()
        return True

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_REDSHIFT_DATASETS)
    @ResourcePolicyService.has_resource_permission(GET_REDSHIFT_DATASET)
    def get_redshift_dataset(uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            dataset = RedshiftDatasetRepository.get_redshift_dataset_by_uri(session, uri)
            if dataset.SamlAdminGroupName in context.groups:
                dataset.userRoleForDataset = DatasetRole.Admin.value
            return dataset

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_REDSHIFT_DATASETS)
    @ResourcePolicyService.has_resource_permission(GET_REDSHIFT_DATASET)
    def list_redshift_dataset_tables(uri, filter):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            dataset = RedshiftDatasetRepository.get_redshift_dataset_by_uri(session, uri)
            return RedshiftDatasetRepository.paginated_redshift_dataset_tables(
                session=session, dataset_uri=dataset.datasetUri, data=filter
            )

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_REDSHIFT_DATASETS)
    @ResourcePolicyService.has_resource_permission(GET_REDSHIFT_DATASET)
    def list_redshift_schema_dataset_tables(uri):
        with get_context().db_engine.scoped_session() as session:
            dataset = RedshiftDatasetRepository.get_redshift_dataset_by_uri(session, uri)
            dataset_tables_names = [
                t.name for t in RedshiftDatasetRepository.list_redshift_dataset_tables(session, dataset.datasetUri)
            ]
            connection = RedshiftConnectionRepository.get_redshift_connection(session, dataset.connectionUri)
            environment = EnvironmentService.get_environment_by_uri(session, connection.environmentUri)
            tables = RedshiftData(
                account_id=environment.AwsAccountId, region=environment.region, connection=connection
            ).list_redshift_tables(dataset.schema)
            for table in tables:
                if table['name'] in dataset_tables_names:
                    table.update({'alreadyAdded': True})
                else:
                    table.update({'alreadyAdded': False})
            return tables

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_REDSHIFT_DATASETS)
    @ResourcePolicyService.has_resource_permission(GET_REDSHIFT_DATASET)
    def get_dataset_upvotes(uri):
        with get_context().db_engine.scoped_session() as session:
            return VoteRepository.count_upvotes(session, uri, target_type='redshiftdataset') or 0

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_REDSHIFT_DATASETS)
    @ResourcePolicyService.has_resource_permission(GET_REDSHIFT_DATASET_TABLE)
    def get_redshift_dataset_table(uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            table = RedshiftDatasetRepository.get_redshift_table_by_uri(session, uri)
            return table

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_REDSHIFT_DATASETS)
    @ResourcePolicyService.has_resource_permission(GET_REDSHIFT_DATASET_TABLE)
    def list_redshift_dataset_table_columns(uri, filter):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            table = RedshiftDatasetRepository.get_redshift_table_by_uri(session=session, table_uri=uri)
            dataset = RedshiftDatasetRepository.get_redshift_dataset_by_uri(
                session=session, dataset_uri=table.datasetUri
            )
            connection = RedshiftConnectionRepository.get_redshift_connection(
                session=session, uri=dataset.connectionUri
            )
            columns = RedshiftData(
                account_id=dataset.AwsAccountId, region=dataset.region, connection=connection
            ).list_redshift_table_columns(dataset.schema, table.name)
            return paginate_list(
                items=columns, page_size=filter.get('pageSize', 10), page=filter.get('page', 1)
            ).to_dict()

    @staticmethod
    def _attach_dataset_permissions(session, dataset, environment):
        ResourcePolicyService.attach_resource_policy(
            session=session,
            group=dataset.SamlAdminGroupName,
            permissions=REDSHIFT_DATASET_ALL,
            resource_uri=dataset.datasetUri,
            resource_type=RedshiftDataset.__name__,
        )
        if dataset.stewards and dataset.stewards != dataset.SamlAdminGroupName:
            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=dataset.stewards,
                permissions=REDSHIFT_DATASET_READ,
                resource_uri=dataset.datasetUri,
                resource_type=RedshiftDataset.__name__,
            )

        if environment.SamlGroupName != dataset.SamlAdminGroupName:
            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=environment.SamlGroupName,
                permissions=REDSHIFT_DATASET_ALL,
                resource_uri=dataset.datasetUri,
                resource_type=RedshiftDataset.__name__,
            )

    @staticmethod
    def _attach_table_permissions(session, dataset, environment, table):
        ResourcePolicyService.attach_resource_policy(
            session=session,
            group=dataset.SamlAdminGroupName,
            permissions=REDSHIFT_DATASET_TABLE_ALL,
            resource_uri=table.rsTableUri,
            resource_type=RedshiftTable.__name__,
        )
        if dataset.stewards and dataset.stewards != dataset.SamlAdminGroupName:
            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=dataset.stewards,
                permissions=REDSHIFT_DATASET_TABLE_READ,
                resource_uri=table.rsTableUri,
                resource_type=RedshiftTable.__name__,
            )
        if environment.SamlGroupName != dataset.SamlAdminGroupName:
            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=environment.SamlGroupName,
                permissions=REDSHIFT_DATASET_TABLE_ALL,
                resource_uri=table.rsTableUri,
                resource_type=RedshiftTable.__name__,
            )

    @staticmethod
    def _transfer_stewardship_to_owners(session, dataset):
        env = EnvironmentService.get_environment_by_uri(session, dataset.environmentUri)
        if dataset.stewards != env.SamlGroupName:
            ResourcePolicyService.delete_resource_policy(
                session=session,
                group=dataset.stewards,
                resource_uri=dataset.datasetUri,
            )

        return dataset

    @staticmethod
    def _transfer_stewardship_to_new_stewards(session, dataset, new_stewards):
        if dataset.stewards != dataset.SamlAdminGroupName:
            ResourcePolicyService.delete_resource_policy(
                session=session,
                group=dataset.stewards,
                resource_uri=dataset.datasetUri,
            )
        ResourcePolicyService.attach_resource_policy(
            session=session,
            group=new_stewards,
            permissions=REDSHIFT_DATASET_READ,
            resource_uri=dataset.datasetUri,
            resource_type=RedshiftDataset.__name__,
        )
        return dataset
