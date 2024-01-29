import logging

from botocore.exceptions import ClientError

from dataall.base.aws.sts import SessionHelper
from dataall.modules.dataset_sharing.db.share_object_models import Catalog

log = logging.getLogger(__name__)


class GlueClient:
    def __init__(self, account_id, region, database):
        aws_session = SessionHelper.remote_session(accountid=account_id)
        self._client = aws_session.client('glue', region_name=region)
        self._database = database
        self._account_id = account_id
        self._region = region

    def create_database(self, location):
        try:
            existing_database = self.database_exists()
            if existing_database:
                glue_database_created = True
            else:
                self._create_glue_database(location)
                glue_database_created = True
            return glue_database_created
        except ClientError as e:
            log.error(
                f'Failed to create database {self._database} on account {self._account_id} due to {e}'
            )
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
            log.info(f'Creating Glue database with input: {db_input}')
            response = self._client.create_database(CatalogId=self._account_id, DatabaseInput=db_input)
            log.info(f'response Create Database: {response}')
            return response
        except ClientError as e:
            log.debug(f'Failed to create database {database}', e)
            raise e

    def database_exists(self):
        try:
            self._client.get_database(CatalogId=self._account_id, Name=self._database)
            return True
        except ClientError:
            log.info(f'Database {self._database} does not exist on account {self._account_id}')
            return False

    def table_exists(self, table_name):
        try:
            table = (
                self._client.get_table(
                    CatalogId=self._account_id, DatabaseName=self._database, Name=table_name
                )
            )
            log.info(f'Glue table found: {table_name}')
            return table
        except ClientError:
            log.info(f'Glue table not found: {table_name}')
            return None

    def delete_table(self, table_name):
        database = self._database
        log.info(
            'Deleting table {} in database {}'.format(
                table_name, database
            )
        )
        response = self._client.delete_table(
            CatalogId=self._account_id,
            DatabaseName=database,
            Name=table_name
        )

        return response

    def create_resource_link(self, resource_link_name, resource_link_input):
        account_id = self._account_id
        database = self._database

        log.info(
            f'Creating ResourceLink {resource_link_name} in database {account_id}://{database}'
        )
        try:
            resource_link = self.table_exists(resource_link_name)
            if resource_link:
                log.info(
                    f'ResourceLink {resource_link_name} already exists in database {account_id}://{database}'
                )
            else:
                resource_link = self._client.create_table(
                    CatalogId=account_id,
                    DatabaseName=database,
                    TableInput=resource_link_input,
                )
                log.info(
                    f'Successfully created ResourceLink {resource_link_name} in database {account_id}://{database}'
                )
            return resource_link
        except ClientError as e:
            log.error(
                f'Could not create ResourceLink {resource_link_name} '
                f'in database {account_id}://{database} '
                f'due to: {e}'
            )
            raise e

    def delete_database(self):
        account_id = self._account_id
        database = self._database

        log.info(f'Deleting database {account_id}://{database} ')
        try:
            if self.database_exists():
                self._client.delete_database(CatalogId=account_id, Name=database)
            return True
        except ClientError as e:
            log.error(
                f'Could not delete database {database} '
                f'in account {account_id} '
                f'due to: {e}'
            )
            raise e

    def remove_create_table_default_permissions(self):
        """
        When upgrading to LF tables and database can still have Create Table Default Permissions turned on.
        Unless this setting is removed, the table or database
        can not be shared using LakeFormation.
        :return:
        """
        try:
            account_id = self._account_id
            database = self._database

            log.info(
                f'Removing CreateTableDefaultPermissions in database {database}'
            )

            response = self._client.get_database(CatalogId=account_id, Name=database)
            existing_database_parameters = response['Database']
            existing_database_parameters['CreateTableDefaultPermissions'] = []

            if 'CreateTime' in existing_database_parameters:
                del existing_database_parameters['CreateTime']
            if 'CatalogId' in existing_database_parameters:
                del existing_database_parameters['CatalogId']

            response = self._client.update_database(
                CatalogId=account_id,
                Name=database,
                DatabaseInput=existing_database_parameters
            )

            log.info(
                f'Successfully removed  Create Table Default Permissions and Create Database Default Permissions '
                f'| {response}')

        except ClientError as e:
            log.error(
                f'Could not remove CreateDatabaseDefaultPermissions and/or CreateTableDefaultPermissions '
                f'permission on database in {database} due to {e}'
            )

    def get_source_catalog(self):
        """ Get the source catalog account details """
        try:
            log.info(f'Fetching source catalog details for database {self._database}')
            response = self._client.get_database(CatalogId=self._account_id, Name=self._database)
            linked_database = response.get('Database', {}).get('TargetDatabase', {})
            log.info(f'Fetched source catalog details for database {self._database} are: {linked_database}')
            if linked_database:
                return Catalog(account_id=linked_database.get('CatalogId'),
                               database_name=linked_database.get('DatabaseName'),
                               region=linked_database.get('Region', self._region))

        except self._client.exceptions.EntityNotFoundException as enoFnd:
            log.exception(f'Could not fetch source catalog details for database {self._database} due to {enoFnd}')
            raise enoFnd
        except Exception as e:
            log.exception(f'Error fetching source catalog details for database {self._database} due to {e}')
            raise e
        return None

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
