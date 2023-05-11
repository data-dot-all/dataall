import json
import logging

from dataall.api.Objects.Stack import stack_helper
from dataall.aws.handlers.quicksight import Quicksight
from dataall.aws.handlers.service_handlers import Worker
from dataall.aws.handlers.sts import SessionHelper
from dataall.core.context import get_context
from dataall.core.permission_checker import has_resource_permission
from dataall.db.api import Vote
from dataall.db.exceptions import AWSResourceNotFound, UnauthorizedOperation
from dataall.db.models import Environment, Task
from dataall.modules.dataset_sharing.api.schema import ShareObject
from dataall.modules.datasets import DatasetIndexer, DatasetTableIndexer
from dataall.modules.datasets.api.dataset.enums import DatasetRole
from dataall.modules.datasets.aws.glue_dataset_client import DatasetCrawler
from dataall.modules.datasets.aws.s3_dataset_client import S3DatasetClient
from dataall.modules.datasets.db.dataset_location_repository import DatasetLocationRepository
from dataall.modules.datasets.services.dataset_permissions import CREDENTIALS_DATASET, SYNC_DATASET, CRAWL_DATASET, \
    SUMMARY_DATASET, DELETE_DATASET, SUBSCRIPTIONS_DATASET
from dataall.modules.datasets_base.db.dataset_repository import DatasetRepository
from dataall.modules.datasets_base.db.models import Dataset

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
    def create_dataset(env_uri, data: dict):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            environment = Environment.get_environment_by_uri(session, env_uri)
            DatasetService.check_dataset_account(environment=environment)

            dataset = DatasetRepository.create_dataset(
                session=session,
                username=context.username,
                groups=context.groups,
                uri=env_uri,
                data=data,
                check_perm=True,
            )

            DatasetRepository.create_dataset_stack(session, dataset)

            DatasetIndexer.upsert(
                session=session, dataset_uri=dataset.datasetUri
            )

        DatasetService._deploy_dataset_stack(dataset)

        dataset.userRoleForDataset = DatasetRole.Creator.value

        return dataset

    @staticmethod
    def import_dataset(data):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            environment = Environment.get_environment_by_uri(session, data.get('environmentUri'))
            DatasetService.check_dataset_account(environment=environment)

            dataset = DatasetRepository.create_dataset(
                session=session,
                username=context.username,
                groups=context.groups,
                uri=data.get('environmentUri'),
                data=data,
                check_perm=True,
            )
            dataset.imported = True
            dataset.importedS3Bucket = True if data['bucketName'] else False
            dataset.importedGlueDatabase = True if data['glueDatabaseName'] else False
            dataset.importedKmsKey = True if data['KmsKeyId'] else False
            dataset.importedAdminRole = True if data['adminRoleName'] else False

            DatasetRepository.create_dataset_stack(session, dataset)

            DatasetIndexer.upsert(
                session=session, dataset_uri=dataset.datasetUri
            )

        DatasetService._deploy_dataset_stack(dataset)

        dataset.userRoleForDataset = DatasetRole.Creator.value

        return dataset

    @staticmethod
    def get_dataset(uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            dataset = DatasetRepository.get_dataset(session, uri=uri)
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
            return DatasetRepository.paginated_user_datasets(
                session, context.username, context.groups, uri=None, data=data
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
                username=context.username,
                groups=context.groups,
                uri=dataset_uri,
                data=data,
            )

    @staticmethod
    def update_dataset(uri: str, data: dict):
        with get_context().db_engine.scoped_session() as session:
            dataset = DatasetRepository.get_dataset_by_uri(session, uri)
            environment = Environment.get_environment_by_uri(session, dataset.environmentUri)
            DatasetService.check_dataset_account(environment=environment)
            updated_dataset = DatasetRepository.update_dataset(
                session=session,
                uri=uri,
                data=data,
            )
            DatasetIndexer.upsert(session, dataset_uri=uri)

        DatasetService._deploy_dataset_stack(updated_dataset)

        return updated_dataset

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
                share = ShareObject.get_share_by_dataset_attributes(
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
                username=context.username,
                groups=context.groups,
                uri=uri,
                data={'page': 1, 'pageSize': 10},
                check_perm=None,
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
        context = get_context()
        with context.db_engine.scoped_session() as session:
            return DatasetRepository.paginated_dataset_shares(
                session=session,
                username=context.username,
                groups=context.groups,
                uri=dataset.datasetUri,
                data=data,
                check_perm=True,
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
    def get_dataset_summary(uri: str):
        # TODO THERE WAS NO PERMISSION CHECK!!!
        with get_context().db_engine.scoped_session() as session:
            dataset = DatasetRepository.get_dataset_by_uri(session, uri)
            environment = Environment.get_environment_by_uri(
                session, dataset.environmentUri
            )

            pivot_session = SessionHelper.remote_session(dataset.AwsAccountId)
            env_admin_session = SessionHelper.get_session(
                base_session=pivot_session,
                role_arn=environment.EnvironmentDefaultIAMRoleArn,
            )
            s3 = env_admin_session.client('s3', region_name=dataset.region)

            try:
                s3.head_object(
                    Bucket=environment.EnvironmentDefaultBucketName,
                    Key=f'summary/{uri}/summary.md',
                )
                response = s3.get_object(
                    Bucket=environment.EnvironmentDefaultBucketName,
                    Key=f'summary/{uri}/summary.md',
                )
                content = str(response['Body'].read().decode('utf-8'))
                return content
            except Exception as e:
                raise e

    @staticmethod
    @has_resource_permission(SUMMARY_DATASET)
    def save_dataset_summary(uri: str, content: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            dataset = DatasetRepository.get_dataset_by_uri(session, uri)
            environment = Environment.get_environment_by_uri(
                session, dataset.environmentUri
            )

            pivot_session = SessionHelper.remote_session(dataset.AwsAccountId)
            env_admin_session = SessionHelper.get_session(
                base_session=pivot_session,
                role_arn=environment.EnvironmentDefaultIAMRoleArn,
            )
            s3 = env_admin_session.client('s3', region_name=dataset.region)

            s3.put_object(
                Bucket=environment.EnvironmentDefaultBucketName,
                Key=f'summary/{uri}/summary.md',
                Body=content,
            )
        return True

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
            env: Environment = Environment.get_environment_by_uri(
                session, dataset.environmentUri
            )
            shares = DatasetRepository.list_dataset_shares_with_existing_shared_items(session, uri)
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

            DatasetService.delete_dataset(
                session=session,
                username=context.username,
                groups=context.groups,
                uri=uri,
                data=None,
                check_perm=True,
            )

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
    def list_datasets_created_in_environment(env_uri: str, data: dict):
        with get_context().db_engine.scoped_session() as session:
            return DatasetRepository.paginated_environment_datasets(
                session=session,
                uri=env_uri,
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
