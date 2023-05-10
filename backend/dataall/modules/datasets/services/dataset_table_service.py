import json
import logging

from botocore.exceptions import ClientError
from pyathena import connect

from dataall.aws.handlers.service_handlers import Worker
from dataall.aws.handlers.sts import SessionHelper
from dataall.core.context import get_context
from dataall.db import models
from dataall.db.api import ResourcePolicy, Environment
from dataall.modules.datasets import DatasetTableIndexer
from dataall.modules.datasets.db.dataset_service import DatasetService
from dataall.modules.datasets.db.dataset_table_repository import DatasetTableRepository
from dataall.modules.datasets.services.dataset_permissions import UPDATE_DATASET_TABLE
from dataall.modules.datasets_base.db.models import Dataset, DatasetTable
from dataall.modules.datasets_base.services.permissions import PREVIEW_DATASET_TABLE
from dataall.utils import json_utils

log = logging.getLogger(__name__)


class DatasetTableService:

    @staticmethod
    def create_table(dataset_uri: str, table_data: dict):
        with get_context().db_engine.scoped_session() as session:
            table = DatasetTableRepository.create_dataset_table(
                session=session,
                uri=dataset_uri,
                data=table_data,
            )
        DatasetTableIndexer.upsert(session, table_uri=table.tableUri)
        return table

    @staticmethod
    def list_dataset_tables(dataset_uri: str, filter: dict):
        with get_context().db_engine.scoped_session() as session:
            return DatasetTableRepository.list_dataset_tables(
                session=session,
                uri=dataset_uri,
                data=filter,
            )

    @staticmethod
    def get_table(table_uri: str):
        with get_context().db_engine.scoped_session() as session:
            table = DatasetTableRepository.get_dataset_table_by_uri(session, table_uri)
            return DatasetTableRepository.get_dataset_table(
                session=session,
                uri=table.datasetUri,
                data={
                    'tableUri': table_uri,
                },
            )

    @staticmethod
    def update_table(table_uri: str, input: dict = None):
        with get_context().db_engine.scoped_session() as session:
            table = DatasetTableRepository.get_dataset_table_by_uri(session, table_uri)
            dataset = DatasetService.get_dataset_by_uri(session, table.datasetUri)

            input['table'] = table
            input['tableUri'] = table.tableUri

            DatasetTableRepository.update_dataset_table(
                session=session,
                uri=dataset.datasetUri,
                data=input,
            )
        DatasetTableIndexer.upsert(session, table_uri=table.tableUri)
        return table

    @staticmethod
    def delete_table(table_uri: str):
        with get_context().db_engine.scoped_session() as session:
            table = DatasetTableRepository.get_dataset_table_by_uri(session, table_uri)
            DatasetTableRepository.delete_dataset_table(
                session=session,
                uri=table.datasetUri,
                data={
                    'tableUri': table_uri,
                },
            )
        DatasetTableIndexer.delete_doc(doc_id=table_uri)
        return True

    @staticmethod
    def preview(table_uri: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            table: DatasetTable = DatasetTableRepository.get_dataset_table_by_uri(
                session, table_uri
            )
            dataset = DatasetService.get_dataset_by_uri(session, table.datasetUri)
            if (
                    dataset.confidentiality
                    != models.ConfidentialityClassification.Unclassified.value
            ):
                ResourcePolicy.check_user_resource_permission(
                    session=session,
                    username=context.username,
                    groups=context.groups,
                    resource_uri=table.tableUri,
                    permission_name=PREVIEW_DATASET_TABLE,
                )
            env = Environment.get_environment_by_uri(session, dataset.environmentUri)
            env_workgroup = {}
            boto3_session = SessionHelper.remote_session(accountid=table.AWSAccountId)
            creds = boto3_session.get_credentials()
            try:
                env_workgroup = boto3_session.client(
                    'athena', region_name=env.region
                ).get_work_group(WorkGroup=env.EnvironmentDefaultAthenaWorkGroup)
            except ClientError as e:
                log.info(
                    f'Workgroup {env.EnvironmentDefaultAthenaWorkGroup} can not be found'
                    f'due to: {e}'
                )

            connection = connect(
                aws_access_key_id=creds.access_key,
                aws_secret_access_key=creds.secret_key,
                aws_session_token=creds.token,
                work_group=env_workgroup.get('WorkGroup', {}).get('Name', 'primary'),
                s3_staging_dir=f's3://{env.EnvironmentDefaultBucketName}/preview/{dataset.datasetUri}/{table.tableUri}',
                region_name=table.region,
            )
            cursor = connection.cursor()

            sql = f'select * from "{table.GlueDatabaseName}"."{table.GlueTableName}" limit 50'  # nosec
            cursor.execute(sql)
            fields = []
            for f in cursor.description:
                fields.append(json.dumps({'name': f[0]}))
            rows = []
            for row in cursor:
                rows.append(json.dumps(json_utils.to_json(list(row))))

        return {'rows': rows, 'fields': fields}

    @staticmethod
    def get_glue_table_properties(table_uri: str):
        with get_context().db_engine.scoped_session() as session:
            table: DatasetTable = DatasetTableRepository.get_dataset_table_by_uri(
                session, table_uri
            )
            return json_utils.to_string(table.GlueTableProperties).replace('\\', ' ')

    @staticmethod
    def publish_table_update(table_uri: str):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            table: DatasetTable = DatasetTableRepository.get_dataset_table_by_uri(
                session, table_uri
            )
            ResourcePolicy.check_user_resource_permission(
                session=session,
                username=context.username,
                groups=context.groups,
                resource_uri=table.datasetUri,
                permission_name=UPDATE_DATASET_TABLE,
            )
            dataset = DatasetService.get_dataset_by_uri(session, table.datasetUri)
            env = Environment.get_environment_by_uri(session, dataset.environmentUri)
            if not env.subscriptionsEnabled or not env.subscriptionsProducersTopicName:
                raise Exception(
                    'Subscriptions are disabled. '
                    "First enable subscriptions for this dataset's environment then retry."
                )

            task = models.Task(
                targetUri=table.datasetUri,
                action='sns.dataset.publish_update',
                payload={'s3Prefix': table.S3Prefix},
            )
            session.add(task)

        Worker.process(engine=context.db_engine, task_ids=[task.taskUri], save_response=False)
        return True

    @staticmethod
    def list_shared_tables_by_env_dataset(dataset_uri: str, env_uri: str):
        with get_context().db_engine.scoped_session() as session:
            return DatasetTableRepository.get_dataset_tables_shared_with_env(
                session,
                dataset_uri,
                env_uri
            )


