import json
import logging

from botocore.exceptions import ClientError
from pyathena import connect

from .... import db
from ..Dataset.resolvers import get_dataset
from ....api.context import Context
from ....aws.handlers.service_handlers import Worker
from ....aws.handlers.sts import SessionHelper
from ....db import permissions, models
from ....db.api import ResourcePolicy, Glossary
from ....searchproxy import indexers
from ....utils import json_utils, sql_utils

log = logging.getLogger(__name__)


def create_table(context, source, datasetUri: str = None, input: dict = None):
    with context.engine.scoped_session() as session:
        table = db.api.DatasetTable.create_dataset_table(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=datasetUri,
            data=input,
            check_perm=True,
        )
        indexers.upsert_table(session, context.es, table.tableUri)
    return table


def list_dataset_tables(context, source, filter: dict = None):
    if not source:
        return None
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return db.api.DatasetTable.list_dataset_tables(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=source.datasetUri,
            data=filter,
            check_perm=True,
        )


def get_table(context, source: models.Dataset, tableUri: str = None):
    with context.engine.scoped_session() as session:
        table = db.api.DatasetTable.get_dataset_table_by_uri(session, tableUri)
        return db.api.DatasetTable.get_dataset_table(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=table.datasetUri,
            data={
                'tableUri': tableUri,
            },
            check_perm=True,
        )


def update_table(context, source, tableUri: str = None, input: dict = None):
    with context.engine.scoped_session() as session:
        table = db.api.DatasetTable.get_dataset_table_by_uri(session, tableUri)

        dataset = db.api.Dataset.get_dataset_by_uri(session, table.datasetUri)

        input['table'] = table
        input['tableUri'] = table.tableUri

        db.api.DatasetTable.update_dataset_table(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=dataset.datasetUri,
            data=input,
            check_perm=True,
        )
        indexers.upsert_table(session, context.es, table.tableUri)
    return table


def delete_table(context, source, tableUri: str = None):
    with context.engine.scoped_session() as session:
        table = db.api.DatasetTable.get_dataset_table_by_uri(session, tableUri)
        db.api.DatasetTable.delete_dataset_table(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=table.datasetUri,
            data={
                'tableUri': tableUri,
            },
            check_perm=True,
        )
    indexers.delete_doc(es=context.es, doc_id=tableUri)
    return True


def preview(context, source, tableUri: str = None):
    with context.engine.scoped_session() as session:
        table: models.DatasetTable = db.api.DatasetTable.get_dataset_table_by_uri(
            session, tableUri
        )
        dataset = db.api.Dataset.get_dataset_by_uri(session, table.datasetUri)
        if (
            dataset.confidentiality
            != models.ConfidentialityClassification.Unclassified.value
        ):
            ResourcePolicy.check_user_resource_permission(
                session=session,
                username=context.username,
                groups=context.groups,
                resource_uri=table.tableUri,
                permission_name=permissions.PREVIEW_DATASET_TABLE,
            )
        env = db.api.Environment.get_environment_by_uri(session, dataset.environmentUri)
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

        SQL = 'select * from {table_identifier} limit 50'.format(
            table_identifier=sql_utils.Identifier(table.GlueDatabaseName, table.GlueTableName)
        )
        cursor.execute(SQL)
        fields = []
        for f in cursor.description:
            fields.append(json.dumps({'name': f[0]}))
        rows = []
        for row in cursor:
            rows.append(json.dumps(json_utils.to_json(list(row))))

    return {'rows': rows, 'fields': fields}


def get_glue_table_properties(context: Context, source: models.DatasetTable, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        table: models.DatasetTable = db.api.DatasetTable.get_dataset_table_by_uri(
            session, source.tableUri
        )
        return json_utils.to_string(table.GlueTableProperties).replace('\\', ' ')


def resolve_dataset(context, source: models.DatasetTable, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        dataset_with_role = get_dataset(
            context, source=None, datasetUri=source.datasetUri
        )
        if not dataset_with_role:
            return None
    return dataset_with_role


def resolve_glossary_terms(context: Context, source: models.DatasetTable, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return Glossary.get_glossary_terms_links(
            session, source.tableUri, 'DatasetTable'
        )


def publish_table_update(context: Context, source, tableUri: str = None):
    with context.engine.scoped_session() as session:
        table: models.DatasetTable = db.api.DatasetTable.get_dataset_table_by_uri(
            session, tableUri
        )
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=table.datasetUri,
            permission_name=permissions.UPDATE_DATASET_TABLE,
        )
        dataset = db.api.Dataset.get_dataset_by_uri(session, table.datasetUri)
        env = db.api.Environment.get_environment_by_uri(session, dataset.environmentUri)
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

    Worker.process(engine=context.engine, task_ids=[task.taskUri], save_response=False)
    return True


def resolve_redshift_copy_schema(context, source: models.DatasetTable, clusterUri: str):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return db.api.RedshiftCluster.get_cluster_dataset_table(
            session, clusterUri, source.datasetUri, source.tableUri
        ).schema


def resolve_redshift_copy_location(
    context, source: models.DatasetTable, clusterUri: str
):
    with context.engine.scoped_session() as session:
        return db.api.RedshiftCluster.get_cluster_dataset_table(
            session, clusterUri, source.datasetUri, source.tableUri
        ).dataLocation


def list_shared_tables_by_env_dataset(context: Context, source, datasetUri: str, envUri: str, filter: dict = None):
    with context.engine.scoped_session() as session:
        return db.api.DatasetTable.get_dataset_tables_shared_with_env(
            session,
            envUri,
            datasetUri
        )
