import json
import logging
from datetime import datetime, timedelta

from botocore.exceptions import ClientError

from common.aws_handlers.service_handlers import Worker
from common.aws_handlers.sts import SessionHelper

log = logging.getLogger(__name__)


class Redshift:
    def __init__(self):
        pass


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
