import json
import logging

from dataall.base.context import get_context
from dataall.base.db import exceptions
from dataall.base.utils.naming_convention import NamingConventionPattern
from dataall.base.aws.quicksight import QuicksightClient
from dataall.base.aws.sts import SessionHelper
from dataall.core.environment.env_permission_checker import has_group_permission
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.permissions.db.resource_policy_repositories import ResourcePolicy
from dataall.core.permissions.permission_checker import has_resource_permission, has_tenant_permission
from dataall.core.stacks.api import stack_helper
from dataall.core.stacks.db.keyvaluetag_repositories import KeyValueTag
from dataall.core.stacks.db.stack_repositories import Stack
from dataall.core.tasks.db.task_models import Task
from dataall.core.tasks.service_handlers import Worker
from dataall.modules.catalog.db.glossary_repositories import GlossaryRepository
from dataall.modules.vote.db.vote_repositories import VoteRepository

from dataall.modules.datasets_base.db.dataset_base_repositories import DatasetBaseRepository
from dataall.modules.datasets_base.services.datasets_base_enums import DatasetRole
from dataall.modules.datasets_base.services.dataset_base_service import DatasetBaseService
from dataall.modules.datasets_base.services.dataset_base_permissions import (
    DELETE_DATASET,
    MANAGE_DATASETS,
    UPDATE_DATASET,
    CREATE_DATASET,
    DATASET_ALL,
    DATASET_READ,
    IMPORT_DATASET,
)
from dataall.modules.s3_datasets.db.dataset_models import S3Dataset, DatasetTable
from dataall.modules.s3_datasets.db.dataset_repositories import S3DatasetRepository
from dataall.modules.s3_datasets.db.dataset_bucket_repositories import DatasetBucketRepository
from dataall.modules.s3_datasets.db.dataset_location_repositories import DatasetLocationRepository
from dataall.modules.s3_datasets.db.dataset_table_repositories import DatasetTableRepository
from dataall.modules.s3_datasets.aws.glue_dataset_client import DatasetCrawler
from dataall.modules.s3_datasets.aws.s3_dataset_client import S3DatasetClient
from dataall.modules.s3_datasets.aws.kms_dataset_client import KmsDatasetClient
from dataall.modules.s3_datasets.indexers.dataset_indexer import DatasetIndexer
from dataall.modules.s3_datasets.services.dataset_permissions import (
    CREDENTIALS_DATASET,
    CRAWL_DATASET,
    DATASET_TABLE_READ
)

from dataall.modules.dataset_sharing_base.db.share_object_base_models import ShareObject
from dataall.modules.dataset_sharing_base.db.share_object_base_repositories import ShareObjectRepository
from dataall.modules.dataset_sharing_base.services.share_base_permissions import SHARE_OBJECT_APPROVER

log = logging.getLogger(__name__)


class S3DatasetService(DatasetBaseService):
    """
    Service class that contains the business logic for managing S3 datasets
    """
    @staticmethod
    def _check_dataset_account(session, environment):
        dashboards_enabled = EnvironmentService.get_boolean_env_param(session, environment, 'dashboardsEnabled')
        if dashboards_enabled:
            quicksight_subscription = QuicksightClient.check_quicksight_enterprise_subscription(
                AwsAccountId=environment.AwsAccountId, region=environment.region
            )
            if quicksight_subscription:
                group = QuicksightClient.create_quicksight_group(
                    AwsAccountId=environment.AwsAccountId, region=environment.region
                )
                return True if group else False
        return True

    @staticmethod
    def _check_imported_resources(dataset: S3Dataset):
        if dataset.importedGlueDatabase:
            if len(dataset.GlueDatabaseName) > NamingConventionPattern.GLUE.value.get('max_length'):
                raise exceptions.InvalidInput(
                    param_name='GlueDatabaseName',
                    param_value=dataset.GlueDatabaseName,
                    constraint=f"less than {NamingConventionPattern.GLUE.value.get('max_length')} characters",
                )
        kms_alias = dataset.KmsAlias

        s3_encryption, kms_id = S3DatasetClient(dataset).get_bucket_encryption()
        if kms_alias not in [None, 'Undefined', '', 'SSE-S3']:  # user-defined KMS encryption
            if s3_encryption == 'AES256':
                raise exceptions.InvalidInput(
                    param_name='KmsAlias',
                    param_value=dataset.KmsAlias,
                    constraint=f'empty, Bucket {dataset.S3BucketName} is encrypted with AWS managed key (SSE-S3). KmsAlias {kms_alias} should NOT be provided as input parameter.',
                )

            key_exists = KmsDatasetClient(account_id=dataset.AwsAccountId, region=dataset.region).check_key_exists(
                key_alias=f'alias/{kms_alias}'
            )
            if not key_exists:
                raise exceptions.AWSResourceNotFound(
                    action=IMPORT_DATASET,
                    message=f'KMS key with alias={kms_alias} cannot be found - Please check if KMS Key Alias exists in account {dataset.AwsAccountId}',
                )

            key_id = KmsDatasetClient(account_id=dataset.AwsAccountId, region=dataset.region).get_key_id(
                key_alias=f'alias/{kms_alias}'
            )

            if key_id != kms_id:
                raise exceptions.InvalidInput(
                    param_name='KmsAlias',
                    param_value=dataset.KmsAlias,
                    constraint=f'the KMS Alias of the KMS key used to encrypt the Bucket {dataset.S3BucketName}. Provide the correct KMS Alias as input parameter.',
                )

        else:  # user-defined S3 encryption
            if s3_encryption != 'AES256':
                raise exceptions.RequiredParameter(param_name='KmsAlias')

        return True

    @staticmethod
    @has_tenant_permission(MANAGE_DATASETS)
    @has_resource_permission(CREATE_DATASET)
    @has_group_permission(CREATE_DATASET)
    def create_dataset(uri, admin_group, data: dict):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            environment = EnvironmentService.get_environment_by_uri(session, uri)
            S3DatasetService._check_dataset_account(session=session, environment=environment)
            dataset = S3DatasetRepository.build_dataset(username=context.username, env=environment, data=data)

            if dataset.imported:
                S3DatasetService._check_imported_resources(dataset)

            dataset = S3DatasetRepository.create_dataset(session=session, env=environment, dataset=dataset, data=data)
            DatasetBaseRepository.create_dataset_lock(session=session, dataset=dataset)

            DatasetBucketRepository.create_dataset_bucket(session, dataset, data)

            ResourcePolicy.attach_resource_policy(
                session=session,
                group=dataset.SamlAdminGroupName,
                permissions=DATASET_ALL,
                resource_uri=dataset.datasetUri,
                resource_type=S3Dataset.__name__,
            )
            if dataset.stewards and dataset.stewards != dataset.SamlAdminGroupName:
                ResourcePolicy.attach_resource_policy(
                    session=session,
                    group=dataset.stewards,
                    permissions=DATASET_READ,
                    resource_uri=dataset.datasetUri,
                    resource_type=S3Dataset.__name__,
                )

            if environment.SamlGroupName != dataset.SamlAdminGroupName:
                ResourcePolicy.attach_resource_policy(
                    session=session,
                    group=environment.SamlGroupName,
                    permissions=DATASET_ALL,
                    resource_uri=dataset.datasetUri,
                    resource_type=S3Dataset.__name__,
                )

            S3DatasetService._create_dataset_stack(session, dataset)

            DatasetIndexer.upsert(session=session, dataset_uri=dataset.datasetUri)

        S3DatasetService._deploy_dataset_stack(dataset)

        dataset.userRoleForDataset = DatasetRole.Creator.value

        return dataset

    @staticmethod
    def import_dataset(uri, admin_group, data):
        data['imported'] = True
        return S3DatasetService.create_dataset(uri=uri, admin_group=admin_group, data=data)

    @staticmethod
    @has_tenant_permission(MANAGE_DATASETS)
    def get_dataset(uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            dataset = S3DatasetRepository.get_dataset_by_uri(session, uri)
            if dataset.SamlAdminGroupName in context.groups:
                dataset.userRoleForDataset = DatasetRole.Admin.value
            return dataset

    @staticmethod
    def get_file_upload_presigned_url(uri: str, data: dict):
        with get_context().db_engine.scoped_session() as session:
            dataset = S3DatasetRepository.get_dataset_by_uri(session, uri)
            return S3DatasetClient(dataset).get_file_upload_presigned_url(data)

    @staticmethod
    def list_locations(dataset_uri, data: dict):
        with get_context().db_engine.scoped_session() as session:
            return DatasetLocationRepository.paginated_dataset_locations(
                session=session,
                uri=dataset_uri,
                data=data,
            )

    @staticmethod
    def list_tables(dataset_uri, data: dict):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            return S3DatasetRepository.paginated_dataset_tables(
                session=session,
                uri=dataset_uri,
                data=data,
            )

    @staticmethod
    @has_tenant_permission(MANAGE_DATASETS)
    @has_resource_permission(UPDATE_DATASET)
    def update_dataset(uri: str, data: dict):
        with get_context().db_engine.scoped_session() as session:
            dataset = S3DatasetRepository.get_dataset_by_uri(session, uri)
            environment = EnvironmentService.get_environment_by_uri(session, dataset.environmentUri)
            S3DatasetService._check_dataset_account(session=session, environment=environment)

            username = get_context().username
            dataset: S3Dataset = S3DatasetRepository.get_dataset_by_uri(session, uri)
            if data and isinstance(data, dict):
                if data.get('imported', False):
                    S3DatasetService._check_imported_resources(dataset)

                for k in data.keys():
                    if k not in ['stewards', 'KmsAlias']:
                        setattr(dataset, k, data.get(k))

                if data.get('KmsAlias') not in ['Undefined'] and data.get('KmsAlias') != dataset.KmsAlias:
                    dataset.KmsAlias = 'SSE-S3' if data.get('KmsAlias') == '' else data.get('KmsAlias')
                    dataset.importedKmsKey = False if data.get('KmsAlias') == '' else True

                if data.get('stewards') and data.get('stewards') != dataset.stewards:
                    if data.get('stewards') != dataset.SamlAdminGroupName:
                        S3DatasetService._transfer_stewardship_to_new_stewards(session, dataset, data['stewards'])
                        dataset.stewards = data['stewards']
                    else:
                        S3DatasetService._transfer_stewardship_to_owners(session, dataset)
                        dataset.stewards = dataset.SamlAdminGroupName

                ResourcePolicy.attach_resource_policy(
                    session=session,
                    group=dataset.SamlAdminGroupName,
                    permissions=DATASET_ALL,
                    resource_uri=dataset.datasetUri,
                    resource_type=S3Dataset.__name__,
                )
                if data.get('terms'):
                    GlossaryRepository.set_glossary_terms_links(session, username, uri, 'Dataset', data.get('terms'))
                S3DatasetRepository.update_dataset_activity(session, dataset, username)

            DatasetIndexer.upsert(session, dataset_uri=uri)

        S3DatasetService._deploy_dataset_stack(dataset)

        return dataset

    @staticmethod
    def get_dataset_statistics(dataset: S3Dataset):
        with get_context().db_engine.scoped_session() as session:
            count_tables = S3DatasetRepository.count_dataset_tables(session, dataset.datasetUri)
            count_locations = DatasetLocationRepository.count_dataset_locations(session, dataset.datasetUri)
            count_upvotes = VoteRepository.count_upvotes(session, dataset.datasetUri, target_type='dataset')
        return {
            'tables': count_tables or 0,
            'locations': count_locations or 0,
            'upvotes': count_upvotes or 0,
        }

    @staticmethod
    @has_resource_permission(CREDENTIALS_DATASET)
    def get_dataset_assume_role_url(uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            dataset = S3DatasetRepository.get_dataset_by_uri(session, uri)
            if dataset.SamlAdminGroupName not in context.groups:
                share = ShareObjectRepository.get_share_by_dataset_attributes(
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
            else:
                role_arn = dataset.IAMDatasetAdminRoleArn
                account_id = dataset.AwsAccountId

        pivot_session = SessionHelper.remote_session(account_id)
        aws_session = SessionHelper.get_session(base_session=pivot_session, role_arn=role_arn)
        url = SessionHelper.get_console_access_url(
            aws_session,
            region=dataset.region,
            bucket=dataset.S3BucketName,
        )
        return url

    @staticmethod
    @has_resource_permission(CRAWL_DATASET)
    def start_crawler(uri: str, data: dict = None):
        engine = get_context().db_engine
        with engine.scoped_session() as session:
            dataset = S3DatasetRepository.get_dataset_by_uri(session, uri)

            location = (
                f's3://{dataset.S3BucketName}/{data.get("prefix")}'
                if data.get('prefix')
                else f's3://{dataset.S3BucketName}'
            )

            crawler = DatasetCrawler(dataset).get_crawler()
            if not crawler:
                raise exceptions.AWSResourceNotFound(
                    action=CRAWL_DATASET,
                    message=f'Crawler {dataset.GlueCrawlerName} can not be found',
                )

            task = Task(
                targetUri=uri,
                action='glue.crawler.start',
                payload={'location': location},
            )
            session.add(task)
            session.commit()

            Worker.queue(engine=engine, task_ids=[task.taskUri])

            return {
                'Name': dataset.GlueCrawlerName,
                'AwsAccountId': dataset.AwsAccountId,
                'region': dataset.region,
                'status': crawler.get('LastCrawl', {}).get('Status', 'N/A'),
            }

    @staticmethod
    @has_resource_permission(CREDENTIALS_DATASET)
    def generate_dataset_access_token(uri):
        with get_context().db_engine.scoped_session() as session:
            dataset = S3DatasetRepository.get_dataset_by_uri(session, uri)

        pivot_session = SessionHelper.remote_session(dataset.AwsAccountId)
        aws_session = SessionHelper.get_session(base_session=pivot_session, role_arn=dataset.IAMDatasetAdminRoleArn)
        c = aws_session.get_credentials()
        credentials = {
            'AccessKey': c.access_key,
            'SessionKey': c.secret_key,
            'sessionToken': c.token,
        }

        return json.dumps(credentials)

    @staticmethod
    def get_dataset_stack(dataset: S3Dataset):
        return stack_helper.get_stack_with_cfn_resources(
            targetUri=dataset.datasetUri,
            environmentUri=dataset.environmentUri,
        )

    @staticmethod
    @has_resource_permission(DELETE_DATASET)
    def delete_dataset(uri: str, delete_from_aws: bool = False):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            dataset: S3Dataset = S3DatasetRepository.get_dataset_by_uri(session, uri)
            env = EnvironmentService.get_environment_by_uri(session, dataset.environmentUri)
            shares = ShareObjectRepository.list_dataset_shares_with_existing_shared_items(
                session=session, dataset_uri=uri
            )
            if shares:
                raise exceptions.UnauthorizedOperation(
                    action=DELETE_DATASET,
                    message=f'Dataset {dataset.name} is shared with other teams. '
                    'Revoke all dataset shares before deletion.',
                )

            tables = [t.tableUri for t in S3DatasetRepository.get_dataset_tables(session, uri)]
            for tableUri in tables:
                DatasetIndexer.delete_doc(doc_id=tableUri)

            folders = [f.locationUri for f in DatasetLocationRepository.get_dataset_folders(session, uri)]
            for folderUri in folders:
                DatasetIndexer.delete_doc(doc_id=folderUri)

            DatasetIndexer.delete_doc(doc_id=uri)

            ShareObjectRepository.delete_shares_with_no_shared_items(session, uri)
            S3DatasetService._delete_dataset_term_links(session, uri)
            DatasetTableRepository.delete_dataset_tables(session, dataset.datasetUri)
            DatasetLocationRepository.delete_dataset_locations(session, dataset.datasetUri)
            DatasetBucketRepository.delete_dataset_buckets(session, dataset.datasetUri)
            KeyValueTag.delete_key_value_tags(session, dataset.datasetUri, 'dataset')
            VoteRepository.delete_votes(session, dataset.datasetUri, 'dataset')

            ResourcePolicy.delete_resource_policy(session=session, resource_uri=uri, group=dataset.SamlAdminGroupName)
            env = EnvironmentService.get_environment_by_uri(session, dataset.environmentUri)
            if dataset.SamlAdminGroupName != env.SamlGroupName:
                ResourcePolicy.delete_resource_policy(session=session, resource_uri=uri, group=env.SamlGroupName)
            if dataset.stewards:
                ResourcePolicy.delete_resource_policy(session=session, resource_uri=uri, group=dataset.stewards)
            DatasetBaseRepository.delete_dataset_lock(session=session, dataset=dataset)
            S3DatasetRepository.delete_dataset(session, dataset)

        if delete_from_aws:
            stack_helper.delete_stack(
                target_uri=uri,
                accountid=env.AwsAccountId,
                cdk_role_arn=env.CDKRoleArn,
                region=env.region,
            )
            stack_helper.deploy_stack(dataset.environmentUri)
        return True

    @staticmethod
    def _deploy_dataset_stack(dataset: S3Dataset):
        """
        Each dataset stack deployment triggers environment stack update
        to rebuild teams IAM roles data access policies
        """
        stack_helper.deploy_stack(dataset.datasetUri)
        stack_helper.deploy_stack(dataset.environmentUri)

    @staticmethod
    def _create_dataset_stack(session, dataset: S3Dataset) -> Stack:
        return Stack.create_stack(
            session=session,
            environment_uri=dataset.environmentUri,
            target_uri=dataset.datasetUri,
            target_label=dataset.label,
            target_type='dataset',
            payload={
                'bucket_name': dataset.S3BucketName,
                'database_name': dataset.GlueDatabaseName,
                'role_name': dataset.S3BucketName,
                'user_name': dataset.S3BucketName,
            },
        )

    @staticmethod
    def _transfer_stewardship_to_owners(session, dataset):
        env = EnvironmentService.get_environment_by_uri(session, dataset.environmentUri)
        if dataset.stewards != env.SamlGroupName:
            ResourcePolicy.delete_resource_policy(
                session=session,
                group=dataset.stewards,
                resource_uri=dataset.datasetUri,
            )

        # Remove Steward Resource Policy on Dataset Tables
        dataset_tables = [t.tableUri for t in S3DatasetRepository.get_dataset_tables(session, dataset.datasetUri)]
        for tableUri in dataset_tables:
            if dataset.stewards != env.SamlGroupName:
                ResourcePolicy.delete_resource_policy(
                    session=session,
                    group=dataset.stewards,
                    resource_uri=tableUri,
                )

        # Remove Steward Resource Policy on Dataset Share Objects
        dataset_shares = ShareObjectRepository.find_dataset_shares(session, dataset.datasetUri)
        if dataset_shares:
            for share in dataset_shares:
                ResourcePolicy.delete_resource_policy(
                    session=session,
                    group=dataset.stewards,
                    resource_uri=share.shareUri,
                )
        return dataset

    @staticmethod
    def _transfer_stewardship_to_new_stewards(session, dataset, new_stewards):
        env = EnvironmentService.get_environment_by_uri(session, dataset.environmentUri)
        if dataset.stewards != dataset.SamlAdminGroupName:
            ResourcePolicy.delete_resource_policy(
                session=session,
                group=dataset.stewards,
                resource_uri=dataset.datasetUri,
            )
        ResourcePolicy.attach_resource_policy(
            session=session,
            group=new_stewards,
            permissions=DATASET_READ,
            resource_uri=dataset.datasetUri,
            resource_type=S3Dataset.__name__,
        )

        dataset_tables = [t.tableUri for t in S3DatasetRepository.get_dataset_tables(session, dataset.datasetUri)]
        for tableUri in dataset_tables:
            if dataset.stewards != dataset.SamlAdminGroupName:
                ResourcePolicy.delete_resource_policy(
                    session=session,
                    group=dataset.stewards,
                    resource_uri=tableUri,
                )
            ResourcePolicy.attach_resource_policy(
                session=session,
                group=new_stewards,
                permissions=DATASET_TABLE_READ,
                resource_uri=tableUri,
                resource_type=DatasetTable.__name__,
            )

        dataset_shares = ShareObjectRepository.find_dataset_shares(session, dataset.datasetUri)
        if dataset_shares:
            for share in dataset_shares:
                ResourcePolicy.attach_resource_policy(
                    session=session,
                    group=new_stewards,
                    permissions=SHARE_OBJECT_APPROVER,
                    resource_uri=share.shareUri,
                    resource_type=ShareObject.__name__,
                )
                if dataset.stewards != dataset.SamlAdminGroupName:
                    ResourcePolicy.delete_resource_policy(
                        session=session,
                        group=dataset.stewards,
                        resource_uri=share.shareUri,
                    )
        return dataset

    @staticmethod
    def _delete_dataset_term_links(session, dataset_uri):
        tables = [t.tableUri for t in S3DatasetRepository.get_dataset_tables(session, dataset_uri)]
        for table_uri in tables:
            GlossaryRepository.delete_glossary_terms_links(session, table_uri, 'DatasetTable')
        GlossaryRepository.delete_glossary_terms_links(session, dataset_uri, 'Dataset')

    #TODO: move this logic to s3_dataset_sharing to avoid circular dependencies

    # @staticmethod
    # @has_tenant_permission(MANAGE_DATASETS)
    # @has_resource_permission(UPDATE_DATASET)
    # def verify_dataset_share_objects(uri: str, share_uris: list):
    #     with get_context().db_engine.scoped_session() as session:
    #         for share_uri in share_uris:
    #             share = ShareObjectRepository.get_share_by_uri(session, share_uri)
    #             states = ShareItemSM.get_share_item_revokable_states()
    #             items = ShareObjectRepository.list_shareable_items(
    #                 session, share, states, {'pageSize': 1000, 'isShared': True}
    #             )
    #             item_uris = [item.shareItemUri for item in items.get('nodes', [])]
    #             ShareItemService.verify_items_share_object(uri=share_uri, item_uris=item_uris)
    #     return True
