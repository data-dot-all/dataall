import json
import logging
from datetime import datetime, timedelta

from botocore.exceptions import ClientError

from ... import db
from ...db import models
from .glue import Glue
from .service_handlers import Worker
from .sts import SessionHelper

log = logging.getLogger(__name__)


class Redshift:
    def __init__(self):
        pass

    @staticmethod
    def get_cluster_from_task(engine, task: models.Task):
        with engine.scoped_session() as session:
            cluster: models.RedshiftCluster = (
                db.api.RedshiftCluster.get_redshift_cluster_by_uri(
                    session=session, uri=task.targetUri
                )
            )
            return cluster

    @staticmethod
    def describe_clusters(**data):
        accountid = data['accountid']
        region = data.get('region', 'eu-west-1')
        session = SessionHelper.remote_session(accountid)
        client_redshift = session.client('redshift', region_name=region)
        if data.get('cluster_id'):
            try:
                response = client_redshift.describe_clusters(
                    ClusterIdentifier=data.get('cluster_id'), MaxRecords=21
                )
                return response.get('Clusters')[0]
            except ClientError as e:
                log.error(e, exc_info=True)
                raise e
        else:
            clusters = []
            try:
                marker = None
                is_pagination_available = True
                while is_pagination_available:
                    paginator = client_redshift.get_paginator('describe_clusters')
                    response_iterator = paginator.paginate(
                        PaginationConfig={'PageSize': 50, 'StartingToken': marker}
                    )
                    for page in response_iterator:
                        if 'Clusters' in page.keys():
                            for cluster in page.get('Clusters'):
                                clusters.append(cluster)
                            try:
                                marker = page['Marker']
                            except KeyError:
                                is_pagination_available = False
                return clusters
            except ClientError as e:
                log.error(e, exc_info=True)
                raise e

    @staticmethod
    def pause_cluster(**data):
        accountid = data['accountid']
        region = data.get('region', 'eu-west-1')
        session = SessionHelper.remote_session(accountid)
        client_redshift = session.client('redshift', region_name=region)
        try:
            response = client_redshift.pause_cluster(
                ClusterIdentifier=data['cluster_id']
            )
            return response
        except ClientError as e:
            log.error(e, exc_info=True)
            raise e

    @staticmethod
    def reboot_cluster(**data):
        accountid = data['accountid']
        region = data.get('region', 'eu-west-1')
        session = SessionHelper.remote_session(accountid)
        client_redshift = session.client('redshift', region_name=region)
        try:
            response = client_redshift.reboot_cluster(
                ClusterIdentifier=data['cluster_id']
            )
            return response
        except ClientError as e:
            log.error(e, exc_info=True)
            raise e

    @staticmethod
    def resume_cluster(**data):
        accountid = data['accountid']
        region = data.get('region', 'eu-west-1')
        session = SessionHelper.remote_session(accountid)
        client_redshift = session.client('redshift', region_name=region)
        try:
            response = client_redshift.resume_cluster(
                ClusterIdentifier=data['cluster_id']
            )
            return response
        except ClientError as e:
            log.error(e, exc_info=True)
            raise e

    @staticmethod
    def get_cluster_credentials(**data):
        try:
            secretsmanager = SessionHelper.remote_session(data['accountid']).client(
                'secretsmanager', region_name=data['region']
            )
            dh_secret = secretsmanager.get_secret_value(SecretId=data['secret_name'])
            credentials = json.loads(dh_secret['SecretString'])
            password = credentials['password']
            return password
        except ClientError as e:
            log.error(e, exc_info=True)
            raise e

    @staticmethod
    def run_query(**data):

        log.info(f"Starting query run: {data.get('sql_query')}")

        accountid = data['accountid']
        region = data.get('region', 'eu-west-1')
        session = SessionHelper.remote_session(accountid)
        client_redshift = session.client('redshift', region_name=region)
        client_redshift_data = session.client('redshift-data', region_name=region)
        try:
            response = client_redshift.describe_clusters(
                ClusterIdentifier=data['cluster_id'], MaxRecords=100
            )
            cluster = response.get('Clusters')[0]
            database = data.get('database', cluster.get('DBName'))
            statement = dict(
                ClusterIdentifier=data['cluster_id'],
                Database=database,
                Sql=data.get('sql_query'),
                WithEvent=data.get('with_event', False),
            )
            if data.get('dbuser'):
                statement['DbUser'] = data.get('dbuser')
            else:
                statement['SecretArn'] = data['secret_arn']
            response = client_redshift_data.execute_statement(**statement)
            log.info(f'Ran query successfully {response}')
        except ClientError as e:
            log.error(e, exc_info=True)
            raise e

    @staticmethod
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

    @staticmethod
    def _init_database(cluster, database_name, database_user, password):
        queries = list()
        queries.append(f'DROP DATABASE IF EXISTS {database_name}')
        queries.append(f'DROP USER IF EXISTS {database_user}')
        queries.append(f'create user {database_user} password disable')
        queries.append(f'create database {database_name} with owner {database_user}')
        queries.append(
            f'GRANT ALL PRIVILEGES ON database {database_name} TO {database_user}'
        )
        queries.append(
            f"ALTER USER {database_user} WITH PASSWORD '{password}' "
            f"VALID UNTIL '{(datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d %H:%M')}'"
        )
        queries.append(
            f'GRANT ALL PRIVILEGES ON database {database_name} TO GROUP PUBLIC'
        )
        log.info(f'Queries for database {cluster.databaseName} init: {queries} ')
        for query in queries:
            Redshift.run_query(
                **{
                    'accountid': cluster.AwsAccountId,
                    'region': cluster.region,
                    'cluster_id': cluster.name,
                    'database': cluster.masterDatabaseName,
                    'dbuser': cluster.masterUsername,
                    'sql_query': query,
                }
            )
        cluster.external_schema_created = True

    @staticmethod
    @Worker.retry(exception=ClientError, tries=4, delay=3, backoff=2, logger=log)
    def get_secret(cluster, secretsmanager):
        try:
            dh_secret = secretsmanager.get_secret_value(SecretId=cluster.datahubSecret)
            return dh_secret
        except ClientError as e:
            log.warning(f'Failed to get secret {cluster.datahubSecret}')
            raise e

    @staticmethod
    def set_cluster_secrets(secretsmanager, cluster: models.RedshiftCluster):
        cluster_secrets = secretsmanager.list_secrets(
            MaxResults=3,
            Filters=[{'Key': 'tag-value', 'Values': [f'{cluster.CFNStackName}']}],
        )
        for s in cluster_secrets['SecretList']:
            if f'{cluster.name}-redshift-dhuser' in s['Name']:
                cluster.datahubSecret = s['Name']
            if f'{cluster.name}-redshift-masteruser' in s['Name']:
                cluster.masterSecret = s['Name']
        return cluster

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def get_cluster_catalog_databases(session, task):
        try:
            cluster = db.api.RedshiftCluster.get_redshift_cluster_by_uri(
                session, task.targetUri
            )
            env = db.api.Environment.get_environment_by_uri(
                session, cluster.environmentUri
            )
            cluster_datasets = db.api.RedshiftCluster.list_all_cluster_datasets(
                session, cluster.clusterUri
            )
            secretsmanager = SessionHelper.remote_session(cluster.AwsAccountId).client(
                'secretsmanager', region_name=cluster.region
            )
            Redshift.set_cluster_secrets(secretsmanager, cluster)
            catalog_databases = []
            for d in cluster_datasets:
                dataset = db.api.Dataset.get_dataset_by_uri(session, d.datasetUri)
                if dataset.environmentUri != cluster.environmentUri:
                    catalog_databases.append(f'{dataset.GlueDatabaseName}shared')
                else:
                    catalog_databases.append(f'{dataset.GlueDatabaseName}')

            log.info(f'Found Schemas to create with Spectrum {catalog_databases}')
        except ClientError as e:
            log.error(e, exc_info=True)
            raise e
        return catalog_databases, cluster, env

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def get_data_prefix(table: models.RedshiftClusterDatasetTable):
        data_prefix = (
            table.dataLocation
            if '/packages.delta' not in table.dataLocation
            else table.dataLocation.replace('/packages.delta', '')
        )
        data_prefix = (
            data_prefix
            if '/_symlink_format_manifest' not in data_prefix
            else data_prefix.replace('/_symlink_format_manifest', '')
        )
        return data_prefix

    @staticmethod
    def get_create_table_statement(schema, table_name, columns):
        return f'CREATE TABLE IF NOT EXISTS {schema}.{table_name}({columns})'

    @staticmethod
    def get_copy_table_statement(schema, table_name, data_prefix, iam_role_arn):
        return (
            f'COPY {schema}.{table_name} '
            f"FROM '{data_prefix}' "
            f"iam_role '{iam_role_arn}' "
        )

    @staticmethod
    def convert_to_redshift_types(dtypes):
        redshift_sql_map = {
            'long': 'bigint',
            'double': 'bigint',
            'string': 'varchar(max)',
        }
        return (
            redshift_sql_map[dtypes.lower()]
            if redshift_sql_map.get(dtypes.lower())
            else dtypes
        )

    @staticmethod
    def get_merge_table_statements(
        schema, table_name, data_prefix, iam_role_arn, columns
    ):
        statements = list()
        statements.append(
            f"""CREATE TABLE "{schema}"."{table_name}_stage"({columns});"""
        )
        statements.append(
            f"""COPY "{schema}"."{table_name}_stage" FROM '{data_prefix}' iam_role '{iam_role_arn}' format as parquet;"""
        )
        statements.append(
            f"""CREATE TABLE "{schema}"."{table_name}_stage"({columns};"""
        )
        statements.append(
            f"""
                        -- Start a new transaction
                        begin transaction;

                        drop table if exists "{schema}"."{table_name}";

                        -- Insert all the rows from the staging table into the target table
                        alter table "{schema}"."{table_name}_stage" rename to "{table_name}";

                        -- End transaction and commit
                        end transaction;
        """
        )
        return statements
