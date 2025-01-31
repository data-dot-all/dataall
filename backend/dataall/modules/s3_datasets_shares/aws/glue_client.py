import logging

from botocore.exceptions import ClientError

from dataall.base.aws.sts import SessionHelper

log = logging.getLogger(__name__)


class GlueClient:
    def __init__(self, account_id, region, database):
        aws_session = SessionHelper.remote_session(accountid=account_id, region=region)
        self._client = aws_session.client('glue', region_name=region)
        self._database = database
        self._account_id = account_id
        self._region = region

    def create_database(self, location):
        try:
            log.info(f'Creating database {self._database} in account {self._account_id}...')
            existing_database = self.get_glue_database()
            if existing_database:
                glue_database_created = True
            else:
                self._create_glue_database(location)
                glue_database_created = True
            log.info(f'Successfully created database {self._database} in account {self._account_id}')
            return glue_database_created
        except ClientError as e:
            log.error(f'Failed to create database {self._database} in account {self._account_id} due to {e}')
            raise e

    def _create_glue_database(self, location):
        database = self._database
        try:
            db_input = {
                'Name': database,
                'Description': 'dataall database {} '.format(database),
                'CreateTableDefaultPermissions': [],
            }
            if location:
                db_input['LocationUri'] = location
            response = self._client.create_database(CatalogId=self._account_id, DatabaseInput=db_input)
            return response
        except ClientError as e:
            raise e

    def get_glue_database(self):
        try:
            log.info(f'Getting database {self._database} in account {self._account_id}...')
            database = self._client.get_database(CatalogId=self._account_id, Name=self._database)
            return database
        except ClientError:
            log.info(f'Database {self._database} not found in account {self._account_id}')
            return False

    def database_exists(self, database_name):
        try:
            log.info(f'Check database exists {self._database} in account {self._account_id}...')
            self._client.get_database(CatalogId=self._account_id, Name=database_name)
            return True
        except ClientError:
            log.info(f'Database {database_name} not found in account {self._account_id}')
            return False

    def table_exists(self, table_name):
        try:
            log.info(f'Check table exists {table_name} in database {self._database} in account {self._account_id}...')
            table = self._client.get_table(CatalogId=self._account_id, DatabaseName=self._database, Name=table_name)
            log.info(f'Glue table {table_name} found in account {self._account_id} in database {self._database}')
            return table
        except ClientError:
            log.info(f'Glue table not found: {table_name}')
            return None

    def delete_table(self, table_name):
        database = self._database
        try:
            log.info(f'Deleting table {table_name} in database {self._database} in catalog {self._account_id}...')
            response = self._client.delete_table(CatalogId=self._account_id, DatabaseName=database, Name=table_name)
            log.info(
                f'Successfully deleted table {table_name} '
                f'in database {database} '
                f'in catalog {self._account_id} '
                f'response: {response}'
            )
            return response
        except ClientError as e:
            log.error(
                f'Could not delete table {table_name} in database {database} in catalog {self._account_id} due to: {e}'
            )
            raise e

    def create_resource_link(self, resource_link_name, table, catalog_id, database):
        account_id = self._account_id
        shared_database = self._database
        resource_link_input = {
            'Name': resource_link_name,
            'TargetTable': {
                'CatalogId': catalog_id,
                'DatabaseName': database,
                'Name': table.GlueTableName,
            },
        }

        try:
            log.info(f'Creating ResourceLink {resource_link_name}  in database {shared_database}...')
            resource_link = self.table_exists(resource_link_name)
            if resource_link:
                log.info(
                    f'ResourceLink {resource_link_name} '
                    f'in database {account_id}://{shared_database}'
                    f'already exists: {resource_link}'
                )
            else:
                resource_link = self._client.create_table(
                    CatalogId=account_id,
                    DatabaseName=shared_database,
                    TableInput=resource_link_input,
                )
                log.info(
                    f'Successfully created ResourceLink {resource_link_name} '
                    f'in database {account_id}://{shared_database} '
                    f'response: {resource_link}'
                )
            return resource_link
        except ClientError as e:
            log.error(
                f'Could not create ResourceLink {resource_link_name} '
                f'in database {account_id}://{shared_database} '
                f'due to: {e}'
            )
            raise e

    def delete_database(self):
        account_id = self._account_id
        database = self._database
        try:
            log.info(f'Deleting database {self._database} in account {self._account_id}...')
            existing_database = self.get_glue_database()
            if existing_database:
                self._client.delete_database(CatalogId=account_id, Name=database)
            log.info(f'Successfully deleted database {database} in account {account_id}')
            return True
        except ClientError as e:
            log.error(f'Could not delete database {database} in account {account_id} due to: {e}')
            raise e

    def get_source_catalog(self):
        """Get the source catalog account details"""
        try:
            log.info(f'Fetching source catalog details for database {self._database}...')
            response = self._client.get_database(CatalogId=self._account_id, Name=self._database)
            linked_database = response.get('Database', {}).get('TargetDatabase', {})
            log.info(f'Fetched source catalog details for database {self._database} are: {linked_database}...')
            if linked_database:
                return {
                    'account_id': linked_database.get('CatalogId'),
                    'database_name': linked_database.get('DatabaseName'),
                    'region': linked_database.get('Region', self._region),
                }

        except self._client.exceptions.EntityNotFoundException as enoFnd:
            log.exception(f'Could not fetch source catalog details for database {self._database} due to {enoFnd}')
            raise enoFnd
        except Exception as e:
            log.exception(f'Error fetching source catalog details for database {self._database} due to {e}')
            raise e
        return None

    def get_glue_database_from_catalog(self):
        # Check if a catalog account exists and return database accordingly
        try:
            catalog_dict = self.get_source_catalog()

            if catalog_dict is not None:
                return catalog_dict.get('database_name')
            else:
                return self._database
        except Exception as e:
            raise e

    def get_database_tags(self):
        # Get tags from the glue database
        account_id = self._account_id
        database = self._database
        region = self._region

        try:
            log.info(f'Getting tags for database {database}')
            resource_arn = f'arn:aws:glue:{region}:{account_id}:database/{database}'
            response = self._client.get_tags(ResourceArn=resource_arn)
            tags = response['Tags']

            log.info(f'Successfully retrieved tags: {tags}')

            return tags
        except self._client.exceptions.EntityNotFoundException as entNotFound:
            log.exception(f'Could not get tags for database {database} due to {entNotFound}')
            raise entNotFound
        except Exception as e:
            log.exception(f'Error fetching tags for {database} due to {e}')
            raise e
