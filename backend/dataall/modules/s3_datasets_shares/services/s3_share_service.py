import logging

from dataall.base.db import utils, exceptions
from dataall.base.context import get_context
from dataall.base.aws.sts import SessionHelper
from dataall.base.aws.iam import IAM
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.tasks.db.task_models import Task
from dataall.core.tasks.service_handlers import Worker
from dataall.modules.datasets_base.db.dataset_repositories import DatasetBaseRepository
from dataall.modules.datasets_base.services.dataset_list_permissions import LIST_ENVIRONMENT_DATASETS
from dataall.modules.shares_base.db.share_object_models import ShareObject
from dataall.modules.shares_base.db.share_object_repositories import ShareObjectRepository
from dataall.modules.shares_base.db.share_object_item_repositories import ShareObjectItemRepository
from dataall.modules.shares_base.db.share_state_machines_repositories import ShareStatusRepository
from dataall.modules.shares_base.services.share_item_service import ShareItemService
from dataall.modules.shares_base.services.share_permissions import GET_SHARE_OBJECT
from dataall.modules.shares_base.services.shares_enums import (
    ShareableType,
    ShareItemStatus,
)
from dataall.modules.shares_base.db.share_object_models import ShareObjectItem
from dataall.modules.s3_datasets.services.dataset_table_data_filter_enums import DataFilterType

from dataall.modules.s3_datasets.db.dataset_models import DatasetTable, DatasetStorageLocation
from dataall.modules.s3_datasets.db.dataset_repositories import DatasetRepository
from dataall.modules.s3_datasets.db.dataset_table_data_filter_repositories import DatasetTableDataFilterRepository
from dataall.modules.s3_datasets.db.dataset_column_repositories import DatasetColumnRepository
from dataall.modules.s3_datasets.services.dataset_permissions import (
    MANAGE_DATASETS,
    UPDATE_DATASET,
    CREDENTIALS_DATASET,
    DATASET_TABLE_READ,
    DATASET_FOLDER_READ,
    GET_DATASET_TABLE,
)
from dataall.modules.s3_datasets_shares.db.s3_share_object_repositories import S3ShareObjectRepository
from dataall.modules.s3_datasets_shares.aws.glue_client import GlueClient


log = logging.getLogger(__name__)


class S3ShareService:
    @staticmethod
    def delete_dataset_table_read_permission(session, share, tableUri):
        """
        Delete Table permissions to share groups
        """
        other_shares = S3ShareObjectRepository.find_all_other_share_items(
            session,
            not_this_share_uri=share.shareUri,
            item_uri=tableUri,
            share_type=ShareableType.Table.value,
            principal_type='GROUP',
            principal_uri=share.groupUri,
            item_status=[ShareItemStatus.Share_Succeeded.value],
        )
        log.info(f'Table {tableUri} has been shared with group {share.groupUri} in {len(other_shares)} more shares')
        if len(other_shares) == 0:
            log.info('Delete permissions...')
            ResourcePolicyService.delete_resource_policy(session=session, group=share.groupUri, resource_uri=tableUri)

    @staticmethod
    def delete_dataset_folder_read_permission(session, share, locationUri):
        """
        Delete Folder permissions to share groups
        """
        other_shares = S3ShareObjectRepository.find_all_other_share_items(
            session,
            not_this_share_uri=share.shareUri,
            item_uri=locationUri,
            share_type=ShareableType.StorageLocation.value,
            principal_type='GROUP',
            principal_uri=share.groupUri,
            item_status=[ShareItemStatus.Share_Succeeded.value],
        )
        log.info(
            f'Location {locationUri} has been shared with group {share.groupUri} in {len(other_shares)} more shares'
        )
        if len(other_shares) == 0:
            log.info('Delete permissions...')
            ResourcePolicyService.delete_resource_policy(
                session=session,
                group=share.groupUri,
                resource_uri=locationUri,
            )

    @staticmethod
    def attach_dataset_table_read_permission(session, share, tableUri):
        """
        Attach Table permissions to share groups
        """
        existing_policy = ResourcePolicyService.find_resource_policies(
            session,
            group=share.groupUri,
            resource_uri=tableUri,
            resource_type=DatasetTable.__name__,
            permissions=DATASET_TABLE_READ,
        )
        # toDo: separate policies from list DATASET_TABLE_READ, because in future only one of them can be granted (Now they are always granted together)
        if len(existing_policy) == 0:
            log.info(
                f'Attaching new resource permission policy {DATASET_TABLE_READ} to table {tableUri} for group {share.groupUri}'
            )
            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=share.groupUri,
                permissions=DATASET_TABLE_READ,
                resource_uri=tableUri,
                resource_type=DatasetTable.__name__,
            )
        else:
            log.info(
                f'Resource permission policy {DATASET_TABLE_READ} to table {tableUri} for group {share.groupUri} already exists. Skip... '
            )

    @staticmethod
    def attach_dataset_folder_read_permission(session, share, locationUri):
        """
        Attach Folder permissions to share groups
        """
        existing_policy = ResourcePolicyService.find_resource_policies(
            session,
            group=share.groupUri,
            resource_uri=locationUri,
            resource_type=DatasetStorageLocation.__name__,
            permissions=DATASET_FOLDER_READ,
        )
        # toDo: separate policies from list DATASET_TABLE_READ, because in future only one of them can be granted (Now they are always granted together)
        if len(existing_policy) == 0:
            log.info(
                f'Attaching new resource permission policy {DATASET_FOLDER_READ} to folder {locationUri} for group {share.groupUri}'
            )

            ResourcePolicyService.attach_resource_policy(
                session=session,
                group=share.groupUri,
                permissions=DATASET_FOLDER_READ,
                resource_uri=locationUri,
                resource_type=DatasetStorageLocation.__name__,
            )
        else:
            log.info(
                f'Resource permission policy {DATASET_FOLDER_READ} to table {locationUri} for group {share.groupUri} already exists. Skip... '
            )

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_DATASETS)
    @ResourcePolicyService.has_resource_permission(UPDATE_DATASET)
    def verify_dataset_share_objects(uri: str, share_uris: list):
        with get_context().db_engine.scoped_session() as session:
            for share_uri in share_uris:
                share = ShareObjectRepository.get_share_by_uri(session, share_uri)
                states = ShareStatusRepository.get_share_item_revokable_states()
                items = ShareObjectRepository.get_all_share_items_in_share(
                    session=session, share_uri=share.shareUri, status=states
                )
                item_uris = [item.shareItemUri for item in items]
                ShareItemService.verify_items_share_object(uri=share_uri, item_uris=item_uris)
        return True

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_DATASETS)
    @ResourcePolicyService.has_resource_permission(UPDATE_DATASET)
    def reapply_share_items_for_dataset(uri: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            reapply_share_items_task: Task = Task(action='ecs.dataset.share.reapply', targetUri=uri)
            session.add(reapply_share_items_task)
        Worker.queue(engine=context.db_engine, task_ids=[reapply_share_items_task.taskUri])
        return True

    @staticmethod
    @ResourcePolicyService.has_resource_permission(LIST_ENVIRONMENT_DATASETS)
    def list_shared_tables_by_env_dataset(uri: str, dataset_uri: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            log.info(
                S3ShareObjectRepository.query_dataset_tables_shared_with_env(
                    session, uri, dataset_uri, context.username, context.groups
                )
            )
            return [
                {
                    'tableUri': res.tableUri,
                    'GlueTableName': res.GlueTableName
                    + (f'_{res.resourceLinkSuffix}' if res.resourceLinkSuffix else ''),
                }
                for res in S3ShareObjectRepository.query_dataset_tables_shared_with_env(
                    session, uri, dataset_uri, context.username, context.groups
                )
            ]

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_DATASETS)
    @ResourcePolicyService.has_resource_permission(CREDENTIALS_DATASET)
    def get_dataset_shared_assume_role_url(uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            dataset = DatasetRepository.get_dataset_by_uri(session, uri)

            if dataset.SamlAdminGroupName in context.groups:
                role_arn = dataset.IAMDatasetAdminRoleArn
                account_id = dataset.AwsAccountId
                region = dataset.region
            else:
                share = ShareObjectRepository.find_share_by_dataset_attributes(
                    session=session, dataset_uri=uri, dataset_owner=context.username
                )
                shared_environment = EnvironmentService.get_environment_by_uri(
                    session=session, uri=share.environmentUri
                )
                env_group = EnvironmentService.get_environment_group(
                    session=session, group_uri=share.principalId, environment_uri=share.environmentUri
                )
                role_arn = env_group.environmentIAMRoleArn
                account_id = shared_environment.AwsAccountId
                region = shared_environment.region

        pivot_session = SessionHelper.remote_session(account_id, region)
        aws_session = SessionHelper.get_session(base_session=pivot_session, role_arn=role_arn)
        url = SessionHelper.get_console_access_url(
            aws_session,
            region=dataset.region,
            bucket=dataset.S3BucketName,
        )
        return url

    @staticmethod
    @ResourcePolicyService.has_resource_permission(GET_SHARE_OBJECT)
    def get_s3_consumption_data(uri):
        with get_context().db_engine.scoped_session() as session:
            share = ShareObjectRepository.get_share_by_uri(session, uri)
            dataset = DatasetRepository.get_dataset_by_uri(session, share.datasetUri)
            if dataset:
                environment = EnvironmentService.get_environment_by_uri(session, share.environmentUri)
                S3AccessPointName = utils.slugify(
                    share.datasetUri + '-' + share.principalId,
                    max_length=50,
                    lowercase=True,
                    regex_pattern='[^a-zA-Z0-9-]',
                    separator='-',
                )
                # Check if the share was made with a Glue Database
                datasetGlueDatabase = GlueClient(
                    account_id=dataset.AwsAccountId, region=dataset.region, database=dataset.GlueDatabaseName
                ).get_glue_database_from_catalog()

                return {
                    's3AccessPointName': S3AccessPointName,
                    'sharedGlueDatabase': f'{datasetGlueDatabase}_shared',
                    's3bucketName': dataset.S3BucketName,
                }
            return {
                's3AccessPointName': 'Not Created',
                'sharedGlueDatabase': 'Not Created',
                's3bucketName': 'Not Created',
            }

    @staticmethod
    @ResourcePolicyService.has_resource_permission(LIST_ENVIRONMENT_DATASETS)
    def list_shared_databases_tables_with_env_group(uri: str, group_uri: str):
        context = get_context()
        if group_uri not in context.groups:
            raise exceptions.UnauthorizedOperation(
                action='LIST_ENVIRONMENT_GROUP_DATASETS',
                message=f'User: {context.username} is not a member of the owner team',
            )
        with context.db_engine.scoped_session() as session:
            return S3ShareObjectRepository.query_shared_glue_databases(
                session=session, groups=context.groups, env_uri=uri, group_uri=group_uri
            )

    @staticmethod
    @ResourcePolicyService.has_resource_permission(GET_DATASET_TABLE)
    def paginate_active_columns_for_table_share(uri: str, shareUri: str, filter=None):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            share_item: ShareObjectItem = ShareObjectRepository.find_sharable_item(session, shareUri, uri)
            filtered_columns = []
            if share_item.attachedDataFilterUri:
                item_data_filter = ShareObjectItemRepository.get_share_item_filter_by_uri(
                    session, share_item.attachedDataFilterUri
                )
                for filter_uri in item_data_filter.dataFilterUris:
                    data_filter = DatasetTableDataFilterRepository.get_data_filter_by_uri(
                        session, filter_uri=filter_uri
                    )
                    if data_filter.filterType == DataFilterType.ROW.value:
                        filtered_columns = None
                        break
                    elif data_filter.filterType == DataFilterType.COLUMN.value:
                        filtered_columns.extend(data_filter.includedCols)
            if filtered_columns:
                filter['filteredColumns'] = list(set(filtered_columns))
            return DatasetColumnRepository.paginate_active_columns_for_table(session, uri, filter)

    @staticmethod
    @ResourcePolicyService.has_resource_permission(
        GET_SHARE_OBJECT, parent_resource=ShareItemService._get_share_uri_from_item_filter_uri
    )
    def list_table_data_filters_by_attached(uri: str, data: dict):
        with get_context().db_engine.scoped_session() as session:
            item_data_filter = ShareObjectItemRepository.get_share_item_filter_by_uri(session, uri)
            data['filterUris'] = item_data_filter.dataFilterUris
            return DatasetTableDataFilterRepository.paginated_data_filters(
                session, table_uri=item_data_filter.itemUri, data=data
            )

    @staticmethod
    def resolve_shared_db_name(GlueDatabaseName: str, shareUri: str):
        with get_context().db_engine.scoped_session() as session:
            share = ShareObjectRepository.get_share_by_uri(session, shareUri)
            dataset = DatasetBaseRepository.get_dataset_by_uri(session, share.datasetUri)
            try:
                datasetGlueDatabase = GlueClient(
                    account_id=dataset.AwsAccountId, region=dataset.region, database=GlueDatabaseName
                ).get_glue_database_from_catalog()
            except Exception as e:
                log.info(f'Error while calling the get_glue_database_from_catalog when resolving db name due to: {e}')
                datasetGlueDatabase = GlueDatabaseName
            return datasetGlueDatabase + '_shared'

    @staticmethod
    def verify_principal_role(session, share: ShareObject) -> bool:
        log.info('Verifying principal IAM role...')
        role_name = share.principalRoleName
        env = EnvironmentService.get_environment_by_uri(session, share.environmentUri)
        principal_role = IAM.get_role_arn_by_name(account_id=env.AwsAccountId, region=env.region, role_name=role_name)
        return principal_role is not None
