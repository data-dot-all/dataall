import logging

from botocore.exceptions import ClientError

from .service_handlers import Worker
from .sts import SessionHelper
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
    def delete_table(accountid, region, database, tablename):
        session = SessionHelper.remote_session(accountid=accountid)
        client = session.client('glue', region_name=region)
        log.info(
            'Deleting table {} in database {}'.format(
                tablename, database
            )
        )
        response = client.delete_table(
            CatalogId=accountid,
            DatabaseName=database,
            Name=tablename
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
            except ClientError as e:
                log.warning(f'Could not retrieve pipeline runs , {str(e)}')
                return []
            return response['JobRuns']
