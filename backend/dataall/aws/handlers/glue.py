import logging

from botocore.exceptions import ClientError

from .sts import SessionHelper

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
