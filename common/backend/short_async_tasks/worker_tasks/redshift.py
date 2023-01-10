import json
import logging
from datetime import datetime, timedelta

from botocore.exceptions import ClientError

from .handle_glue_table_schema import Glue
from backend.short_async_tasks import Worker
from backend.aws import SessionHelper, Redshift


from ... import db
from ...db import models

log = logging.getLogger(__name__)


@Worker.handler(path='redshift.cluster.init_database')
def init_datahub_db(engine, task: models.Task):
    with engine.scoped_session() as session:
        cluster: models.RedshiftCluster = (
            db.api.RedshiftCluster.get_redshift_cluster_by_uri(
                session=session, uri=task.targetUri
            )
        )
        secretsmanager = SessionHelper.remote_session(cluster.AwsAccountId).client(
            'secretsmanager', region_name=cluster.region
        )
        dh_secret = Redshift.get_secret(cluster, secretsmanager)
        credentials = json.loads(dh_secret['SecretString'])
        password = credentials['password']
        log.info(f'Starting {cluster.databaseName} name creation... ')
        Redshift._init_database(
            cluster, cluster.databaseName, cluster.databaseUser, password
        )
        session.commit()


@Worker.retry(exception=ClientError, tries=4, delay=3, backoff=2, logger=log)
def get_secret(cluster, secretsmanager):
    try:
        dh_secret = secretsmanager.get_secret_value(SecretId=cluster.datahubSecret)
        return dh_secret
    except ClientError as e:
        log.warning(f'Failed to get secret {cluster.datahubSecret}')
        raise e


@Worker.handler(path='redshift.cluster.create_external_schema')
def create_external_schemas(engine, task):
    with engine.scoped_session() as session:
        catalog_databases, cluster, env = Redshift.get_cluster_catalog_databases(
            session, task
        )
        Redshift.run_query(
            **{
                'accountid': cluster.AwsAccountId,
                'region': cluster.region,
                'cluster_id': cluster.name,
                'database': cluster.databaseName,
                'dbuser': cluster.masterUsername,
                'sql_query': f'CREATE SCHEMA dataall_{cluster.clusterUri.lower()}',
            }
        )
        Redshift.run_query(
            **{
                'accountid': cluster.AwsAccountId,
                'region': cluster.region,
                'cluster_id': cluster.name,
                'database': cluster.databaseName,
                'dbuser': cluster.masterUsername,
                'sql_query': f'GRANT ALL ON SCHEMA dataall_{cluster.clusterUri.lower()} TO {cluster.databaseUser} ',
            }
        )
        for database in catalog_databases:
            Redshift.run_query(
                **{
                    'accountid': cluster.AwsAccountId,
                    'region': cluster.region,
                    'cluster_id': cluster.name,
                    'database': cluster.databaseName,
                    'dbuser': cluster.masterUsername,
                    'sql_query': f'drop schema if exists {database}',
                }
            )
            Redshift.run_query(
                **{
                    'accountid': cluster.AwsAccountId,
                    'region': cluster.region,
                    'cluster_id': cluster.name,
                    'database': cluster.databaseName,
                    'dbuser': cluster.masterUsername,
                    'sql_query': f'create external schema {database} '
                    f"from data catalog database '{database}' iam_role "
                    f"'{env.EnvironmentDefaultIAMRoleArn}' ",
                }
            )
            Redshift.run_query(
                **{
                    'accountid': cluster.AwsAccountId,
                    'region': cluster.region,
                    'cluster_id': cluster.name,
                    'database': cluster.databaseName,
                    'dbuser': cluster.masterUsername,
                    'sql_query': f'GRANT ALL ON SCHEMA {database} TO {cluster.databaseUser} ',
                }
            )
            Redshift.run_query(
                **{
                    'accountid': cluster.AwsAccountId,
                    'region': cluster.region,
                    'cluster_id': cluster.name,
                    'database': cluster.databaseName,
                    'dbuser': cluster.masterUsername,
                    'sql_query': f'GRANT ALL ON SCHEMA {database} TO GROUP PUBLIC ',
                }
            )
        return True

@Worker.handler(path='redshift.cluster.drop_external_schema')
def drop_external_schemas(engine, task):
    with engine.scoped_session() as session:
        catalog_databases, cluster, env = Redshift.get_cluster_catalog_databases(
            session, task
        )
        database = task.payload['database']
        kill_sessionsquery = (
            f'SELECT pg_terminate_backend(pg_stat_activity.procpid) '
            f'FROM pg_stat_activity '
            f"WHERE pg_stat_activity.datname = '{database}' "
            f"AND pg_stat_activity.usename = '{cluster.databaseUser}' "
            f'AND procpid <> pg_backend_pid();'
        )
        Redshift.run_query(
            **{
                'accountid': cluster.AwsAccountId,
                'region': cluster.region,
                'cluster_id': cluster.name,
                'database': cluster.databaseName,
                'dbuser': cluster.masterUsername,
                'sql_query': kill_sessionsquery,
            }
        )
        Redshift.run_query(
            **{
                'accountid': cluster.AwsAccountId,
                'region': cluster.region,
                'cluster_id': cluster.name,
                'database': cluster.databaseName,
                'dbuser': cluster.masterUsername,
                'sql_query': f'REVOKE ALL ON SCHEMA {database} TO {cluster.databaseUser} ',
            }
        )
        Redshift.run_query(
            **{
                'accountid': cluster.AwsAccountId,
                'region': cluster.region,
                'cluster_id': cluster.name,
                'database': cluster.databaseName,
                'dbuser': cluster.masterUsername,
                'sql_query': f'drop schema {database}',
            }
        )
        return True


@Worker.handler(path='redshift.cluster.tag')
def tag_cluster(engine, task):
    with engine.scoped_session() as session:
        cluster = db.api.RedshiftCluster.get_redshift_cluster_by_uri(
            session, task.targetUri
        )
        try:
            accountid = cluster.AwsAccountId
            region = cluster.region
            session = SessionHelper.remote_session(accountid)
            client_redshift = session.client('redshift', region_name=region)
            client_redshift.create_tags(
                ResourceName=f'arn:aws:redshift:{region}:{accountid}:cluster:{cluster.name}',
                Tags=[{'Key': 'dataall', 'Value': 'true'}],
            )
        except ClientError as e:
            log.error(e, exc_info=True)
            raise e


@Worker.handler(path='redshift.iam_roles.update')
def update_cluster_roles(engine, task: models.Task):
    with engine.scoped_session() as session:
        cluster = db.api.RedshiftCluster.get_redshift_cluster_by_uri(
            session, task.targetUri
        )
        environment: models.Environment = session.query(models.Environment).get(
            cluster.environmentUri
        )
        log.info(
            f'Updating cluster {cluster.name}|{environment.AwsAccountId} '
            f'with environment role {environment.EnvironmentDefaultIAMRoleArn}'
        )
        try:
            accountid = cluster.AwsAccountId
            region = cluster.region
            aws_session = SessionHelper.remote_session(accountid)
            client_redshift = aws_session.client('redshift', region_name=region)
            client_redshift.modify_cluster_iam_roles(
                ClusterIdentifier=cluster.name,
                AddIamRoles=[
                    environment.EnvironmentDefaultIAMRoleArn,
                ],
            )
            log.info(
                f'Successfully Updated cluster {cluster.name}|{environment.AwsAccountId} '
                f'with environment role {environment.EnvironmentDefaultIAMRoleArn}'
            )
        except ClientError as e:
            log.error(e, exc_info=True)
            raise e


@Worker.handler(path='redshift.subscriptions.copy')
def copy_data(engine, task: models.Task):
    with engine.scoped_session() as session:

        environment: models.Environment = session.query(models.Environment).get(
            task.targetUri
        )

        dataset: models.Dataset = db.api.Dataset.get_dataset_by_uri(
            session, task.payload['datasetUri']
        )

        table: models.DatasetTable = db.api.DatasetTable.get_dataset_table_by_uri(
            session, task.payload['tableUri']
        )

        env_clusters = (
            session.query(models.RedshiftCluster)
            .filter(
                models.RedshiftCluster.environmentUri == environment.environmentUri,
            )
            .all()
        )

        log.info(f"Received Message {task.payload['message']}")

        message = task.payload['message']

        if not message:
            raise Exception('Task message can not be found')

        glue_table = Glue.table_exists(
            **{
                'accountid': table.AWSAccountId,
                'region': table.region,
                'database': table.GlueDatabaseName,
                'tablename': table.GlueTableName,
            }
        )
        columns = (
            glue_table.get('Table').get('StorageDescriptor', {}).get('Columns')
        )
        log.info(f'Glue table columns: {columns}')

        ddl_columns = ','.join(
            [
                f"{col['Name']} {Redshift.convert_to_redshift_types(col['Type'])}"
                for col in columns
            ]
        )
        log.info(f'DDL Columns: {ddl_columns}')

        for cluster in env_clusters:
            cluster_dataset_table = (
                db.api.RedshiftCluster.get_cluster_dataset_table(
                    session, cluster.clusterUri, dataset.datasetUri, table.tableUri
                )
            )
            if cluster_dataset_table:
                log.info(
                    f'Cluster {cluster}|{environment.AwsAccountId} '
                    f'copy from {dataset.name} for table {table.GlueTableName} is enabled'
                )
                queries = list()
                queries.append(
                    f'CREATE SCHEMA IF NOT EXISTS {cluster_dataset_table.schema}'
                )
                queries.append(
                    f'GRANT ALL ON SCHEMA {cluster_dataset_table.schema} TO {cluster.databaseUser}'
                )
                queries.append(
                    f'GRANT ALL ON SCHEMA {cluster_dataset_table.schema} TO GROUP PUBLIC'
                )
                queries.append(
                    Redshift.get_create_table_statement(
                        cluster_dataset_table.schema,
                        table.GlueTableName,
                        ddl_columns,
                    )
                )
                queries.append(
                    f'GRANT ALL ON TABLE {cluster_dataset_table.schema}.{table.GlueTableName} TO {cluster.databaseUser}'
                )
                queries.append(
                    f'GRANT ALL ON TABLE {cluster_dataset_table.schema}.{table.GlueTableName} TO GROUP PUBLIC'
                )
                data_prefix = Redshift.get_data_prefix(cluster_dataset_table)
                queries.extend(
                    Redshift.get_merge_table_statements(
                        cluster_dataset_table.schema,
                        table.GlueTableName,
                        data_prefix,
                        environment.EnvironmentDefaultIAMRoleArn,
                        ddl_columns,
                    )
                )
                for query in queries:
                    Redshift.run_query(
                        **{
                            'accountid': cluster.AwsAccountId,
                            'region': cluster.region,
                            'cluster_id': cluster.name,
                            'database': cluster.databaseName,
                            'dbuser': cluster.databaseUser,
                            'sql_query': query,
                        }
                    )
    return True
