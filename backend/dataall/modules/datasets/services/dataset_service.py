import json
import logging

from dataall.api.Objects.Stack import stack_helper
from dataall.aws.handlers.quicksight import Quicksight
from dataall.aws.handlers.service_handlers import Worker
from dataall.aws.handlers.sts import SessionHelper
from dataall.core.context import get_context
from dataall.core.permission_checker import has_resource_permission, has_tenant_permission, has_group_permission
from dataall.db.api import Vote, ResourcePolicy, KeyValueTag, Stack, Environment
from dataall.db.exceptions import AWSResourceNotFound, UnauthorizedOperation
from dataall.db.models import Task
from dataall.modules.dataset_sharing.db.models import ShareObject
from dataall.modules.dataset_sharing.db.share_object_repository import ShareObjectRepository
from dataall.modules.dataset_sharing.services.share_permissions import SHARE_OBJECT_APPROVER
from dataall.modules.datasets.aws.glue_dataset_client import DatasetCrawler
from dataall.modules.datasets.aws.s3_dataset_client import S3DatasetClient
from dataall.modules.datasets.db.dataset_location_repository import DatasetLocationRepository
from dataall.modules.datasets.db.dataset_table_repository import DatasetTableRepository
from dataall.modules.datasets.indexers.dataset_indexer import DatasetIndexer
from dataall.modules.datasets.indexers.table_indexer import DatasetTableIndexer
from dataall.modules.datasets.services.dataset_permissions import CREDENTIALS_DATASET, SYNC_DATASET, CRAWL_DATASET, \
    DELETE_DATASET, SUBSCRIPTIONS_DATASET, MANAGE_DATASETS, UPDATE_DATASET, LIST_ENVIRONMENT_DATASETS, \
    CREATE_DATASET, DATASET_ALL, DATASET_READ
from dataall.modules.datasets_base.db.dataset_repository import DatasetRepository
from dataall.modules.datasets_base.db.enums import DatasetRole
from dataall.modules.datasets_base.db.models import Dataset, DatasetTable
from dataall.modules.datasets_base.services.permissions import DATASET_TABLE_READ

log = logging.getLogger(__name__)


class DatasetService:

    @staticmethod
    def check_dataset_account(environment):
        if environment.dashboardsEnabled:
            quicksight_subscription = Quicksight.check_quicksight_enterprise_subscription(
                AwsAccountId=environment.AwsAccountId)
            if quicksight_subscription:
                group = Quicksight.create_quicksight_group(AwsAccountId=environment.AwsAccountId)
                return True if group else False
        return True

    @staticmethod
    @has_tenant_permission(MANAGE_DATASETS)
    @has_resource_permission(CREATE_DATASET)
    @has_group_permission(CREATE_DATASET)
    def create_dataset(uri, admin_group, data: dict):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            environment = Environment.get_environment_by_uri(session, uri)
            DatasetService.check_dataset_account(environment=environment)

            dataset = DatasetRepository.create_dataset(
                session=session,
                username=context.username,
                uri=uri,
                data=data,
            )

            ResourcePolicy.attach_resource_policy(
                session=session,
                group=data['SamlAdminGroupName'],
                permissions=DATASET_ALL,
                resource_uri=dataset.datasetUri,
                resource_type=Dataset.__name__,
            )
            if dataset.stewards and dataset.stewards != dataset.SamlAdminGroupName:
                ResourcePolicy.attach_resource_policy(
                    session=session,
                    group=dataset.stewards,
                    permissions=DATASET_READ,
                    resource_uri=dataset.datasetUri,
                    resource_type=Dataset.__name__,
                )
            if environment.SamlGroupName != dataset.SamlAdminGroupName:
                ResourcePolicy.attach_resource_policy(
                    session=session,
                    group=environment.SamlGroupName,
                    permissions=DATASET_ALL,
                    resource_uri=dataset.datasetUri,
                    resource_type=Dataset.__name__,
                )

            DatasetService._create_dataset_stack(session, dataset)

            DatasetIndexer.upsert(
                session=session, dataset_uri=dataset.datasetUri
            )

        DatasetService._deploy_dataset_stack(dataset)

        dataset.userRoleForDataset = DatasetRole.Creator.value

        return dataset

    @staticmethod
    def import_dataset(uri, admin_group, data):
        data['imported'] = True
        return DatasetService.create_dataset(uri=uri, admin_group=admin_group, data=data)

    @staticmethod
    @has_tenant_permission(MANAGE_DATASETS)
    def get_dataset(uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            dataset = DatasetRepository.get_dataset_by_uri(session, uri)
            if dataset.SamlAdminGroupName in context.groups:
                dataset.userRoleForDataset = DatasetRole.Admin.value
            return dataset

    @staticmethod
    def get_file_upload_presigned_url(uri: str, data: dict):
        with get_context().db_engine.scoped_session() as session:
            dataset = DatasetRepository.get_dataset_by_uri(session, uri)
            return S3DatasetClient(dataset).get_file_upload_presigned_url(data)

    @staticmethod
    def list_datasets(data: dict):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            return ShareObjectRepository.paginated_user_datasets(
                session, context.username, context.groups, data=data
            )

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
            return DatasetRepository.paginated_dataset_tables(
                session=session,
                uri=dataset_uri,
                data=data,
            )

    @staticmethod
    @has_tenant_permission(MANAGE_DATASETS)
    @has_resource_permission(UPDATE_DATASET)
    def update_dataset(uri: str, data: dict):
        with get_context().db_engine.scoped_session() as session:
            dataset = DatasetRepository.get_dataset_by_uri(session, uri)
            environment = Environment.get_environment_by_uri(session, dataset.environmentUri)
            DatasetService.check_dataset_account(environment=environment)

            username = get_context().username
            dataset: Dataset = DatasetRepository.get_dataset_by_uri(session, uri)
            if data and isinstance(data, dict):
                for k in data.keys():
                    if k != 'stewards':
                        setattr(dataset, k, data.get(k))
                if data.get('stewards') and data.get('stewards') != dataset.stewards:
                    if data.get('stewards') != dataset.SamlAdminGroupName:
                        DatasetService._transfer_stewardship_to_new_stewards(
                            session, dataset, data['stewards']
                        )
                        dataset.stewards = data['stewards']
                    else:
                        DatasetService._transfer_stewardship_to_owners(session, dataset)
                        dataset.stewards = dataset.SamlAdminGroupName

                ResourcePolicy.attach_resource_policy(
                    session=session,
                    group=dataset.SamlAdminGroupName,
                    permissions=DATASET_ALL,
                    resource_uri=dataset.datasetUri,
                    resource_type=Dataset.__name__,
                )
                DatasetRepository.update_dataset_glossary_terms(session, username, uri, data)
                DatasetRepository.update_dataset_activity(session, dataset, username)

            DatasetIndexer.upsert(session, dataset_uri=uri)

        DatasetService._deploy_dataset_stack(dataset)

        return dataset

    @staticmethod
    def get_dataset_statistics(dataset: Dataset):
        with get_context().db_engine.scoped_session() as session:
            count_tables = DatasetRepository.count_dataset_tables(session, dataset.datasetUri)
            count_locations = DatasetLocationRepository.count_dataset_locations(
                session, dataset.datasetUri
            )
            count_upvotes = Vote.count_upvotes(
                session, None, None, dataset.datasetUri, {'targetType': 'dataset'}
            )
        return {
            'tables': count_tables or 0,
            'locations': count_locations or 0,
            'upvotes': count_upvotes or 0,
        }

    @staticmethod
    @has_resource_permission(CREDENTIALS_DATASET)
    def get_dataset_etl_credentials(uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            task = Task(targetUri=uri, action='iam.dataset.user.credentials')
            session.add(task)
        response = Worker.process(
            engine=context.db_engine, task_ids=[task.taskUri], save_response=False
        )[0]
        return json.dumps(response['response'])

    @staticmethod
    @has_resource_permission(CREDENTIALS_DATASET)
    def get_dataset_assume_role_url(uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            dataset = DatasetRepository.get_dataset_by_uri(session, uri)
            if dataset.SamlAdminGroupName not in context.groups:
                share = ShareObjectRepository.get_share_by_dataset_attributes(
                    session=session,
                    dataset_uri=uri,
                    dataset_owner=context.username
                )
                shared_environment = Environment.get_environment_by_uri(
                    session=session,
                    uri=share.environmentUri
                )
                env_group = Environment.get_environment_group(
                    session=session,
                    group_uri=share.principalId,
                    environment_uri=share.environmentUri
                )
                role_arn = env_group.environmentIAMRoleArn
                account_id = shared_environment.AwsAccountId
            else:
                role_arn = dataset.IAMDatasetAdminRoleArn
                account_id = dataset.AwsAccountId

        pivot_session = SessionHelper.remote_session(account_id)
        aws_session = SessionHelper.get_session(
            base_session=pivot_session, role_arn=role_arn
        )
        url = SessionHelper.get_console_access_url(
            aws_session,
            region=dataset.region,
            bucket=dataset.S3BucketName,
        )
        return url

    @staticmethod
    @has_resource_permission(SYNC_DATASET)
    def sync_tables(uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            dataset = DatasetRepository.get_dataset_by_uri(session, uri)

            task = Task(
                action='glue.dataset.database.tables',
                targetUri=dataset.datasetUri,
            )
            session.add(task)
        Worker.process(engine=context.db_engine, task_ids=[task.taskUri], save_response=False)
        with context.db_engine.scoped_session() as session:
            DatasetTableIndexer.upsert_all(
                session=session, dataset_uri=dataset.datasetUri
            )
            DatasetTableIndexer.remove_all_deleted(session=session, dataset_uri=dataset.datasetUri)
            return DatasetRepository.paginated_dataset_tables(
                session=session,
                uri=uri,
                data={'page': 1, 'pageSize': 10},
            )

    @staticmethod
    @has_resource_permission(CRAWL_DATASET)
    def start_crawler(uri: str, data: dict = None):
        engine = get_context().db_engine
        with engine.scoped_session() as session:
            dataset = DatasetRepository.get_dataset_by_uri(session, uri)

            location = (
                f's3://{dataset.S3BucketName}/{data.get("prefix")}'
                if data.get('prefix')
                else f's3://{dataset.S3BucketName}'
            )

            crawler = DatasetCrawler(dataset).get_crawler()
            if not crawler:
                raise AWSResourceNotFound(
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
    def list_dataset_share_objects(dataset: Dataset, data: dict = None):
        with get_context().db_engine.scoped_session() as session:
            return ShareObjectRepository.paginated_dataset_shares(
                session=session,
                uri=dataset.datasetUri,
                data=data
            )

    @staticmethod
    @has_resource_permission(CREDENTIALS_DATASET)
    def generate_dataset_access_token(uri):
        with get_context().db_engine.scoped_session() as session:
            dataset = DatasetRepository.get_dataset_by_uri(session, uri)

        pivot_session = SessionHelper.remote_session(dataset.AwsAccountId)
        aws_session = SessionHelper.get_session(
            base_session=pivot_session, role_arn=dataset.IAMDatasetAdminRoleArn
        )
        c = aws_session.get_credentials()
        credentials = {
            'AccessKey': c.access_key,
            'SessionKey': c.secret_key,
            'sessionToken': c.token,
        }

        return json.dumps(credentials)

    @staticmethod
    def get_dataset_stack(dataset: Dataset):
        return stack_helper.get_stack_with_cfn_resources(
            targetUri=dataset.datasetUri,
            environmentUri=dataset.environmentUri,
        )

    @staticmethod
    @has_resource_permission(CRAWL_DATASET)
    def get_crawler(uri: str, name: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            dataset = DatasetRepository.get_dataset_by_uri(session, uri)

        response = DatasetCrawler(dataset).get_crawler(crawler_name=name)
        return {
            'Name': name,
            'AwsAccountId': dataset.AwsAccountId,
            'region': dataset.region,
            'status': response.get('LastCrawl', {}).get('Status', 'N/A'),
        }

    @staticmethod
    @has_resource_permission(DELETE_DATASET)
    def delete_dataset(uri: str, delete_from_aws: bool = False):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            dataset: Dataset = DatasetRepository.get_dataset_by_uri(session, uri)
            env = Environment.get_environment_by_uri(
                session, dataset.environmentUri
            )
            shares = ShareObjectRepository.list_dataset_shares_with_existing_shared_items(session, uri)
            if shares:
                raise UnauthorizedOperation(
                    action=DELETE_DATASET,
                    message=f'Dataset {dataset.name} is shared with other teams. '
                            'Revoke all dataset shares before deletion.',
                )
            redshift_datasets = DatasetRepository.list_dataset_redshift_clusters(
                session, uri
            )
            if redshift_datasets:
                raise UnauthorizedOperation(
                    action=DELETE_DATASET,
                    message='Dataset is used by Redshift clusters. '
                            'Remove clusters associations first.',
                )

            tables = [t.tableUri for t in DatasetRepository.get_dataset_tables(session, uri)]
            for uri in tables:
                DatasetIndexer.delete_doc(doc_id=uri)

            folders = [f.locationUri for f in DatasetLocationRepository.get_dataset_folders(session, uri)]
            for uri in folders:
                DatasetIndexer.delete_doc(doc_id=uri)

            DatasetIndexer.delete_doc(doc_id=uri)

            dataset = DatasetRepository.get_dataset_by_uri(session, uri)
            ShareObjectRepository.delete_shares_with_no_shared_items(session, uri)
            DatasetRepository.delete_dataset_term_links(session, uri)
            DatasetTableRepository.delete_dataset_tables(session, dataset.datasetUri)
            DatasetLocationRepository.delete_dataset_locations(session, dataset.datasetUri)
            KeyValueTag.delete_key_value_tags(session, dataset.datasetUri, 'dataset')
            Vote.delete_votes(session, dataset.datasetUri, 'dataset')

            ResourcePolicy.delete_resource_policy(
                session=session, resource_uri=uri, group=dataset.SamlAdminGroupName
            )
            env = Environment.get_environment_by_uri(session, dataset.environmentUri)
            if dataset.SamlAdminGroupName != env.SamlGroupName:
                ResourcePolicy.delete_resource_policy(
                    session=session, resource_uri=uri, group=env.SamlGroupName
                )
            if dataset.stewards:
                ResourcePolicy.delete_resource_policy(
                    session=session, resource_uri=uri, group=dataset.stewards
                )

            DatasetRepository.delete_dataset(session, dataset)

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
    @has_resource_permission(SUBSCRIPTIONS_DATASET)
    def publish_dataset_update(uri: str, s3_prefix: str):
        engine = get_context().db_engine
        with engine.scoped_session() as session:
            dataset = DatasetRepository.get_dataset_by_uri(session, uri)
            env = Environment.get_environment_by_uri(session, dataset.environmentUri)
            if not env.subscriptionsEnabled or not env.subscriptionsProducersTopicName:
                raise Exception(
                    'Subscriptions are disabled. '
                    "First enable subscriptions for this dataset's environment then retry."
                )

            task = Task(
                targetUri=uri,
                action='sns.dataset.publish_update',
                payload={'s3Prefix': s3_prefix},
            )
            session.add(task)

        response = Worker.process(
            engine=engine, task_ids=[task.taskUri], save_response=False
        )[0]
        log.info(f'Dataset update publish response: {response}')
        return True

    @staticmethod
    def _deploy_dataset_stack(dataset: Dataset):
        """
        Each dataset stack deployment triggers environment stack update
        to rebuild teams IAM roles data access policies
        """
        stack_helper.deploy_stack(dataset.datasetUri)
        stack_helper.deploy_stack(dataset.environmentUri)

    @staticmethod
    def _create_dataset_stack(session, dataset: Dataset) -> Stack:
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
    @has_resource_permission(LIST_ENVIRONMENT_DATASETS)
    def list_datasets_created_in_environment(uri: str, data: dict):
        with get_context().db_engine.scoped_session() as session:
            return DatasetRepository.paginated_environment_datasets(
                session=session,
                uri=uri,
                data=data,
            )

    @staticmethod
    def list_datasets_owned_by_env_group(env_uri: str, group_uri: str, data: dict):
        with get_context().db_engine.scoped_session() as session:
            return DatasetRepository.paginated_environment_group_datasets(
                session=session,
                envUri=env_uri,
                groupUri=group_uri,
                data=data,
            )

    @staticmethod
    def _transfer_stewardship_to_owners(session, dataset):
        dataset_shares = ShareObjectRepository.find_dataset_shares(session, dataset.datasetUri)
        if dataset_shares:
            for share in dataset_shares:
                ResourcePolicy.attach_resource_policy(
                    session=session,
                    group=dataset.SamlAdminGroupName,
                    permissions=SHARE_OBJECT_APPROVER,
                    resource_uri=share.shareUri,
                    resource_type=ShareObject.__name__,
                )
        return dataset

    @staticmethod
    def _transfer_stewardship_to_new_stewards(session, dataset, new_stewards):
        env = Environment.get_environment_by_uri(session, dataset.environmentUri)
        if dataset.stewards != env.SamlGroupName:
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
            resource_type=Dataset.__name__,
        )

        dataset_tables = [t.tableUri for t in DatasetRepository.get_dataset_tables(session, dataset.datasetUri)]
        for tableUri in dataset_tables:
            if dataset.stewards != env.SamlGroupName:
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
                ResourcePolicy.delete_resource_policy(
                    session=session,
                    group=dataset.stewards,
                    resource_uri=share.shareUri,
                )
        return dataset
