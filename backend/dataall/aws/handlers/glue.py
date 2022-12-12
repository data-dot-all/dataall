import logging

from botocore.exceptions import ClientError

from .service_handlers import Worker
from .sts import SessionHelper
from ... import db
from ...db import models

log = logging.getLogger('aws:glue')


class Glue:
    def __init__(self):
        pass

    @staticmethod
    def create_database(accountid, database, region, location):
        try:
            existing_database = Glue.database_exists(
                accountid=accountid, database=database, region=region
            )
            if existing_database:
                glue_database_created = True
            else:
                Glue._create_glue_database(accountid, database, region, location)
                glue_database_created = True
            return glue_database_created
        except ClientError as e:
            log.error(
                f'Failed to create database {database} on account {accountid} due to {e}'
            )
            raise e

    @staticmethod
    def _create_glue_database(accountid, database, region, location):
        try:
            aws_session = SessionHelper.remote_session(accountid=accountid)
            glue = aws_session.client('glue', region_name=region)
            db_input = {
                'Name': database,
                'Description': 'dataall database {} '.format(database),
                'CreateTableDefaultPermissions': [],
            }
            if location:
                db_input['LocationUri'] = location
            log.info(f'Creating Glue database with input: {db_input}')
            response = glue.create_database(CatalogId=accountid, DatabaseInput=db_input)
            log.info(f'response Create Database: {response}')
            return response
        except ClientError as e:
            log.debug(f'Failed to create database {database}', e)
            raise e

    @staticmethod
    def get_database_arn(**data):
        return 'arn:aws:glue:{}:{}:database/{}'.format(
            data.get('region', 'eu-west-1'), data.get('accountid'), data.get('database')
        )

    @staticmethod
    def database_exists(**data):
        accountid = data['accountid']
        database = data.get('database', 'UnknownDatabaseName')
        region = data.get('region', 'eu-west-1')
        session = SessionHelper.remote_session(accountid)
        try:
            glue_client = session.client('glue', region_name=region)
            glue_client.get_database(CatalogId=data['accountid'], Name=database)
            return True
        except ClientError:
            log.info(f'Database {database} does not exist on account {accountid}...')
            return False

    @staticmethod
    @Worker.handler(path='glue.dataset.database.tables')
    def list_tables(engine, task: models.Task):
        with engine.scoped_session() as session:
            dataset: models.Dataset = db.api.Dataset.get_dataset_by_uri(
                session, task.targetUri
            )
            accountid = dataset.AwsAccountId
            region = dataset.region
            tables = Glue.list_glue_database_tables(
                accountid, dataset.GlueDatabaseName, region
            )
            db.api.DatasetTable.sync(session, dataset.datasetUri, glue_tables=tables)
            return tables

    @staticmethod
    def list_glue_database_tables(accountid, database, region):
        aws_session = SessionHelper.remote_session(accountid=accountid)
        glue = aws_session.client('glue', region_name=region)
        found_tables = []
        try:
            log.debug(f'Looking for {database} tables')

            if not Glue.database_exists(
                accountid=accountid, database=database, region=region
            ):
                return found_tables

            paginator = glue.get_paginator('get_tables')

            pages = paginator.paginate(
                DatabaseName=database,
                CatalogId=accountid,
            )
            for page in pages:
                found_tables.extend(page['TableList'])

            log.debug(f'Retrieved all database {database} tables: {found_tables}')

        except ClientError as e:
            log.error(
                f'Failed to retrieve tables for database {accountid}|{database}: {e}',
                exc_info=True,
            )
        return found_tables

    @staticmethod
    def table_exists(**data):
        accountid = data['accountid']
        region = data.get('region', 'eu-west-1')
        database = data.get('database', 'UndefinedDatabaseName')
        table_name = data.get('tablename', 'UndefinedTableName')
        try:
            table = (
                SessionHelper.remote_session(accountid)
                .client('glue', region_name=region)
                .get_table(
                    CatalogId=data['accountid'], DatabaseName=database, Name=table_name
                )
            )
            log.info(f'Glue table found: {data}')
            return table
        except ClientError:
            log.info(f'Glue table not found: {data}')
            return None

    @staticmethod
    def _create_table(**data):
        accountid = data['accountid']
        region = data.get('region', 'eu-west-1')
        database = data.get('database', 'UnknownDatabaseName')

        session = SessionHelper.remote_session(accountid=accountid)
        glue = session.client('glue', region_name=region)
        log.info(
            'Creating table {} in database {}'.format(
                data['tablename'], data['database']
            )
        )
        if not Glue.database_exists(
            database=database, region=region, accountid=accountid
        ):
            Glue.create_database(accountid, database, region, None)
        if 'table_input' not in data:
            table_input = {
                'Name': data['tablename'],
                'Description': data.get('Description', 'Not available'),
                'Parameters': {'classification': 'csv', 'skip.header.line.count': '1'},
                'StorageDescriptor': {
                    'Columns': [
                        {'Name': c['Name'], 'Type': c['Type']}
                        for c in data.get('columns')
                    ],
                    'Location': data.get('location'),
                    'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
                    'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
                    'SerdeInfo': {
                        'SerializationLibrary': 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe',
                        'Parameters': {
                            'serialization.format': ',',
                            'field.delim': ',',
                            'escape.delim': '\\',
                        },
                    },
                },
                'TableType': 'EXTERNAL_TABLE',
                'PartitionKeys': data.get('partition_keys') or [],
            }
        else:
            table_input = data['table_input']

        found_table = Glue.table_exists(**data)

        if not found_table:
            response = glue.create_table(
                CatalogId=accountid,
                DatabaseName=data.get('database'),
                TableInput=table_input,
            )
            log.info(f'Successfully Created table {table_input} on account {accountid}')
            return response

        else:

            if Glue.is_resource_link(found_table):

                log.info(
                    f'Table is a Resource Link {found_table} '
                    f'on account {accountid} and is managed by source account'
                )
                return found_table

            elif Glue.is_resource_link(table_input):

                return Glue.delete_table_and_create_resourcelink(
                    glue, database, accountid, table_input
                )

            else:
                response = glue.update_table(
                    CatalogId=accountid,
                    DatabaseName=data.get('database'),
                    TableInput=table_input,
                )
                log.info(
                    f'Successfully Updated table {found_table} on account {accountid}'
                )
                return response

    @staticmethod
    def create_resource_link(**data):
        accountid = data['accountid']
        region = data['region']
        database = data['database']
        resource_link_name = data['resource_link_name']
        resource_link_input = data['resource_link_input']
        log.info(
            f'Creating ResourceLink {resource_link_name} in database {accountid}://{database}'
        )
        try:
            session = SessionHelper.remote_session(accountid=accountid)
            glue = session.client('glue', region_name=region)
            resource_link = Glue.table_exists(
                accountid=accountid,
                region=region,
                database=database,
                tablename=resource_link_name,
            )
            if resource_link:
                log.info(
                    f'ResourceLink {resource_link_name} already exists in database {accountid}://{database}'
                )
            else:
                resource_link = glue.create_table(
                    CatalogId=accountid,
                    DatabaseName=database,
                    TableInput=resource_link_input,
                )
                log.info(
                    f'Successfully created ResourceLink {resource_link_name} in database {accountid}://{database}'
                )
            return resource_link
        except ClientError as e:
            log.error(
                f'Could not create ResourceLink {resource_link_name} '
                f'in database {accountid}://{database} '
                f'due to: {e}'
            )
            raise e

    @staticmethod
    def is_resource_link(table_input: dict):
        """
        Verifies if a Glue table or Glue table input contains the block "TargetTable"
        if it is the case it means it is a Resource Link
        to a shared table by Lake Formation cross account or from the same account
        :param table_input:
        :return:
        """
        if 'TargetTable' in table_input.keys():
            log.info(
                f"Table {table_input['Name']} is a resource link "
                f"from account {table_input['TargetTable']['CatalogId']} and will not be updated"
            )
            return True
        return False

    @staticmethod
    def delete_table_and_create_resourcelink(glue, database, accountid, table_input):
        """
        When table exists before Lake Formation introduction it needs to be deleted
        And transformed to a resource link
        :param glue:
        :param database:
        :param accountid:
        :param table_input:
        :return:
        """
        try:
            glue.delete_table(
                CatalogId=accountid, DatabaseName=database, Name=table_input['Name']
            )
            log.debug(
                f'Successfully Deleted table {table_input} on account {accountid}'
            )
            response = glue.create_table(
                CatalogId=accountid, DatabaseName=database, TableInput=table_input
            )
            log.info(f'Successfully Changed table to resource link {response}')
            return response
        except ClientError as e:
            log.warning(
                f'Failed to change table to resource link {table_input} due to: {e}'
            )
            raise e

    @staticmethod
    def delete_database(**data):
        accountid = data['accountid']
        region = data['region']
        database = data['database']
        log.info(f'Deleting database {accountid}://{database} ...')
        try:
            session = SessionHelper.remote_session(accountid=accountid)
            glue = session.client('glue', region_name=region)
            if Glue.database_exists(
                accountid=accountid,
                region=region,
                database=database,
            ):
                glue.delete_database(CatalogId=accountid, Name=database)
            return True
        except ClientError as e:
            log.error(
                f'Could not delete database {database} '
                f'in account {accountid} '
                f'due to: {e}'
            )
            raise e

    @staticmethod
    def batch_delete_tables(**data):
        accountid = data['accountid']
        region = data['region']
        database = data['database']
        tables = data['tables']

        if not tables:
            log.info('No tables to delete exiting method...')
            return

        log.info(f'Batch deleting tables: {tables}')
        try:
            session = SessionHelper.remote_session(accountid=accountid)
            glue = session.client('glue', region_name=region)
            if Glue.database_exists(
                accountid=accountid,
                region=region,
                database=database,
            ):
                glue.batch_delete_table(
                    CatalogId=accountid, DatabaseName=database, TablesToDelete=tables
                )
                log.debug(
                    f'Batch deleted tables {len(tables)} from database {database} successfully'
                )
            return True
        except ClientError as e:
            log.error(
                f'Could not batch delete tables {tables} '
                f'in database {accountid}://{database} '
                f'due to: {e}'
            )
            raise e

    @staticmethod
    @Worker.handler(path='glue.dataset.crawler.create')
    def create_crawler(engine, task: models.Task):
        with engine.scoped_session() as session:
            dataset: models.Dataset = db.api.Dataset.get_dataset_by_uri(
                session, task.targetUri
            )
            location = task.payload.get('location')
            Glue.create_glue_crawler(
                **{
                    'crawler_name': f'{dataset.GlueDatabaseName}-{location}'[:52],
                    'region': dataset.region,
                    'accountid': dataset.AwsAccountId,
                    'database': dataset.GlueDatabaseName,
                    'location': location or f's3://{dataset.S3BucketName}',
                }
            )

    @staticmethod
    def create_glue_crawler(**data):
        try:
            accountid = data['accountid']
            database = data.get('database')
            session = SessionHelper.remote_session(accountid=accountid)
            glue = session.client('glue', region_name=data.get('region', 'eu-west-1'))
            crawler_name = data.get('crawler_name')
            targets = {'S3Targets': [{'Path': data.get('location')}]}
            crawler = Glue._get_crawler(glue, crawler_name)
            if crawler:
                Glue._update_existing_crawler(
                    glue, accountid, crawler_name, targets, database
                )
            else:
                crawler = glue.create_crawler(
                    Name=crawler_name,
                    Role=SessionHelper.get_delegation_role_arn(accountid=accountid),
                    DatabaseName=database,
                    Targets=targets,
                    Tags=data.get('tags', {'Application': 'dataall'}),
                )

            glue.start_crawler(Name=crawler_name)
            log.info('Crawler %s started ', crawler_name)
            return crawler
        except ClientError as e:
            log.error('Failed to create Crawler due to %s', e)

    @staticmethod
    def get_glue_crawler(data):
        try:
            accountid = data['accountid']
            session = SessionHelper.remote_session(accountid=accountid)
            glue = session.client('glue', region_name=data.get('region', 'eu-west-1'))
            crawler_name = data.get('crawler_name')
            crawler = Glue._get_crawler(glue, crawler_name)
            return crawler
        except ClientError as e:
            log.error('Failed to find Crawler due to %s', e)
            raise e

    @staticmethod
    @Worker.handler(path='glue.crawler.start')
    def start_crawler(engine, task: models.Task):
        with engine.scoped_session() as session:
            dataset: models.Dataset = db.api.Dataset.get_dataset_by_uri(
                session, task.targetUri
            )
            location = task.payload.get('location')
            return Glue.start_glue_crawler(
                {
                    'crawler_name': dataset.GlueCrawlerName,
                    'region': dataset.region,
                    'accountid': dataset.AwsAccountId,
                    'database': dataset.GlueDatabaseName,
                    'location': location,
                }
            )

    @staticmethod
    def start_glue_crawler(data):
        try:
            accountid = data['accountid']
            crawler_name = data['crawler_name']
            database = data['database']
            targets = {'S3Targets': [{'Path': data.get('location')}]}
            session = SessionHelper.remote_session(accountid=accountid)
            glue = session.client('glue', region_name=data.get('region', 'eu-west-1'))
            if data.get('location'):
                Glue._update_existing_crawler(
                    glue, accountid, crawler_name, targets, database
                )
            crawler = Glue._get_crawler(glue, crawler_name)
            glue.start_crawler(Name=crawler_name)
            log.info('Crawler %s started ', crawler_name)
            return crawler
        except ClientError as e:
            log.error('Failed to start Crawler due to %s', e)
            raise e

    @staticmethod
    def _get_crawler(glue, crawler_name):
        crawler = None
        try:
            crawler = glue.get_crawler(Name=crawler_name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityNotFoundException':
                log.debug(f'Crawler does not exists {crawler_name} %s', e)
            else:
                raise e
        return crawler.get('Crawler') if crawler else None

    @staticmethod
    def _update_existing_crawler(glue, accountid, crawler_name, targets, database):
        try:
            glue.stop_crawler(Name=crawler_name)
        except ClientError as e:
            if (
                e.response['Error']['Code'] == 'CrawlerStoppingException'
                or e.response['Error']['Code'] == 'CrawlerNotRunningException'
            ):
                log.error('Failed to stop crawler %s', e)
        try:
            glue.update_crawler(
                Name=crawler_name,
                Role=SessionHelper.get_delegation_role_arn(accountid=accountid),
                DatabaseName=database,
                Targets=targets,
            )
            log.info('Crawler %s updated ', crawler_name)
        except ClientError as e:
            log.debug('Failed to stop and update crawler %s', e)
            if e.response['Error']['Code'] != 'CrawlerRunningException':
                log.error('Failed to update crawler %s', e)
            else:
                raise e

    @staticmethod
    @Worker.handler('glue.table.update_column')
    def update_table_columns(engine, task: models.Task):
        with engine.scoped_session() as session:
            column: models.DatasetTableColumn = session.query(
                models.DatasetTableColumn
            ).get(task.targetUri)
            table: models.DatasetTable = session.query(models.DatasetTable).get(
                column.tableUri
            )
            try:
                aws_session = SessionHelper.remote_session(table.AWSAccountId)

                Glue.grant_pivot_role_all_table_permissions(aws_session, table)

                glue_client = aws_session.client('glue', region_name=table.region)

                original_table = glue_client.get_table(
                    CatalogId=table.AWSAccountId,
                    DatabaseName=table.GlueDatabaseName,
                    Name=table.name,
                )
                updated_table = {
                    k: v
                    for k, v in original_table['Table'].items()
                    if k
                    not in [
                        'CatalogId',
                        'VersionId',
                        'DatabaseName',
                        'CreateTime',
                        'UpdateTime',
                        'CreatedBy',
                        'IsRegisteredWithLakeFormation',
                    ]
                }
                all_columns = updated_table.get('StorageDescriptor', {}).get(
                    'Columns', []
                ) + updated_table.get('PartitionKeys', [])
                for col in all_columns:
                    if col['Name'] == column.name:
                        col['Comment'] = column.description
                        log.info(
                            f'Found column {column.name} adding description {column.description}'
                        )
                        response = glue_client.update_table(
                            DatabaseName=table.GlueDatabaseName,
                            TableInput=updated_table,
                        )
                        log.info(
                            f'Column {column.name} updated successfully: {response}'
                        )
                return True

            except ClientError as e:
                log.error(
                    f'Failed to update table column {column.name} description: {e}'
                )
                raise e

    @staticmethod
    def grant_pivot_role_all_table_permissions(aws_session, table):
        """
        Pivot role needs to have all permissions
        for tables managed inside dataall
        :param aws_session:
        :param table:
        :return:
        """
        try:
            lf_client = aws_session.client('lakeformation', region_name=table.region)
            grant_dict = dict(
                Principal={
                    'DataLakePrincipalIdentifier': SessionHelper.get_delegation_role_arn(
                        table.AWSAccountId
                    )
                },
                Resource={
                    'Table': {
                        'DatabaseName': table.GlueDatabaseName,
                        'Name': table.name,
                    }
                },
                Permissions=['SELECT', 'ALTER', 'DROP', 'INSERT'],
            )
            response = lf_client.grant_permissions(**grant_dict)
            log.error(
                f'Successfully granted pivot role all table '
                f'aws://{table.AWSAccountId}/{table.GlueDatabaseName}/{table.name} '
                f'access: {response}'
            )
        except ClientError as e:
            log.error(
                f'Failed to grant pivot role all table '
                f'aws://{table.AWSAccountId}/{table.GlueDatabaseName}/{table.name} '
                f'access: {e}'
            )
            raise e

    @staticmethod
    @Worker.handler('glue.table.columns')
    def get_table_columns(engine, task: models.Task):
        with engine.scoped_session() as session:
            dataset_table: models.DatasetTable = session.query(models.DatasetTable).get(
                task.targetUri
            )
            aws = SessionHelper.remote_session(dataset_table.AWSAccountId)
            glue_client = aws.client('glue', region_name=dataset_table.region)
            glue_table = {}
            try:
                glue_table = glue_client.get_table(
                    CatalogId=dataset_table.AWSAccountId,
                    DatabaseName=dataset_table.GlueDatabaseName,
                    Name=dataset_table.name,
                )
            except glue_client.exceptions.ClientError as e:
                log.error(
                    f'Failed to get table aws://{dataset_table.AWSAccountId}'
                    f'//{dataset_table.GlueDatabaseName}'
                    f'//{dataset_table.name} due to: '
                    f'{e}'
                )
            db.api.DatasetTable.sync_table_columns(
                session, dataset_table, glue_table['Table']
            )
        return True

    @staticmethod
    @Worker.handler(path='glue.job.runs')
    def get_job_runs(engine, task: models.Task):
        with engine.scoped_session() as session:
            Data_pipeline: models.DataPipeline = session.query(models.DataPipeline).get(
                task.targetUri
            )
            aws = SessionHelper.remote_session(Data_pipeline.AwsAccountId)
            glue_client = aws.client('glue', region_name=Data_pipeline.region)
            try:
                response = glue_client.get_job_runs(JobName=Data_pipeline.name)
                print(response)
            except ClientError as e:
                log.warning(f'Could not retrieve pipeline runs , {str(e)}')
                return []
            return response['JobRuns']

    @staticmethod
    @Worker.handler('glue.job.start_profiling_run')
    def start_profiling_run(engine, task: models.Task):
        with engine.scoped_session() as session:
            profiling: models.DatasetProfilingRun = (
                db.api.DatasetProfilingRun.get_profiling_run(
                    session, profilingRunUri=task.targetUri
                )
            )
            dataset: models.Dataset = session.query(models.Dataset).get(
                profiling.datasetUri
            )
            run = Glue.run_job(
                **{
                    'accountid': dataset.AwsAccountId,
                    'name': dataset.GlueProfilingJobName,
                    'region': dataset.region,
                    'arguments': (
                        {'--table': profiling.GlueTableName}
                        if profiling.GlueTableName
                        else {}
                    ),
                }
            )
            db.api.DatasetProfilingRun.update_run(
                session,
                profilingRunUri=profiling.profilingRunUri,
                GlueJobRunId=run['JobRunId'],
            )
            return run

    @staticmethod
    def run_job(**data):
        accountid = data['accountid']
        name = data['name']
        try:
            session = SessionHelper.remote_session(accountid=accountid)
            client = session.client('glue', region_name=data.get('region', 'eu-west-1'))
            response = client.start_job_run(
                JobName=name, Arguments=data.get('arguments', {})
            )
            return response
        except ClientError as e:
            log.error(f'Failed to start profiling job {name} due to: {e}')
            raise e

    @staticmethod
    @Worker.handler('glue.job.profiling_run_status')
    def get_profiling_run(engine, task: models.Task):
        with engine.scoped_session() as session:
            profiling: models.DatasetProfilingRun = (
                db.api.DatasetProfilingRun.get_profiling_run(
                    session, profilingRunUri=task.targetUri
                )
            )
            dataset: models.Dataset = session.query(models.Dataset).get(
                profiling.datasetUri
            )
            glue_run = Glue.get_job_run(
                **{
                    'accountid': dataset.AwsAccountId,
                    'name': dataset.GlueProfilingJobName,
                    'region': dataset.region,
                    'run_id': profiling.GlueJobRunId,
                }
            )
            profiling.status = glue_run['JobRun']['JobRunState']
            session.commit()
            return profiling.status

    @staticmethod
    def get_job_run(**data):
        accountid = data['accountid']
        name = data['name']
        run_id = data['run_id']
        try:
            session = SessionHelper.remote_session(accountid=accountid)
            client = session.client('glue', region_name=data.get('region', 'eu-west-1'))
            response = client.get_job_run(JobName=name, RunId=run_id)
            return response
        except ClientError as e:
            log.error(f'Failed to get job run {run_id} due to: {e}')
            raise e

    @staticmethod
    def grant_principals_all_table_permissions(
        table: models.DatasetTable, principals: [str], client=None
    ):
        """
        Update the table permissions on Lake Formation
        for tables managed by data.all
        :param principals:
        :param table:
        :param client:
        :return:
        """
        if not client:
            client = SessionHelper.remote_session(table.AWSAccountId).client(
                'lakeformation', region_name=table.region
            )
        for principal in principals:
            try:
                grant_dict = dict(
                    Principal={'DataLakePrincipalIdentifier': principal},
                    Resource={
                        'Table': {
                            'DatabaseName': table.GlueDatabaseName,
                            'Name': table.name,
                        }
                    },
                    Permissions=['ALL'],
                )
                response = client.grant_permissions(**grant_dict)
                log.error(
                    f'Successfully granted principals {principals} all permissions on table '
                    f'aws://{table.AWSAccountId}/{table.GlueDatabaseName}/{table.name} '
                    f'access: {response}'
                )
            except ClientError as e:
                log.error(
                    f'Failed to grant admin roles {principals} all permissions on table '
                    f'aws://{table.AWSAccountId}/{table.GlueDatabaseName}/{table.name} '
                    f'access: {e}'
                )
