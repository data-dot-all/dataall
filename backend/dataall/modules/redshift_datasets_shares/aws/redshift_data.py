import logging
import time
from botocore.exceptions import ClientError
from dataall.base.aws.sts import SessionHelper
from dataall.modules.redshift_datasets.db.redshift_models import RedshiftConnection

log = logging.getLogger(__name__)


class RedshiftShareDataClient:
    def __init__(self, account_id: str, region: str, connection: RedshiftConnection) -> None:
        session = SessionHelper.remote_session(accountid=account_id, region=region)
        self.client = session.client(service_name='redshift-data', region_name=region)
        self.database = connection.database
        self.execute_connection_params = {
            'Database': connection.database,
        }
        if connection.workgroup:
            self.execute_connection_params['WorkgroupName'] = connection.workgroup
        if connection.clusterId:
            self.execute_connection_params['ClusterIdentifier'] = connection.clusterId
        if connection.secretArn:
            self.execute_connection_params['SecretArn'] = connection.secretArn
        if connection.redshiftUser and connection.clusterId:
            # https://boto3.amazonaws.com/v1/documentation/api/1.26.93/reference/services/redshift-data/client/list_databases.html
            # We cannot use DbUser with serverless for role federation.
            # It must use the current session IAM role, which in this case would be the pivot role.
            self.execute_connection_params['DbUser'] = connection.redshiftUser

    def _execute_statement(self, sql: str):
        log.info(f'Executing {sql=} with connection {self.execute_connection_params}...')
        execute_dict = self.execute_connection_params
        execute_dict['Sql'] = sql
        execute_statement_response = self.client.execute_statement(**execute_dict)

        while (describe_statement_response := self.client.describe_statement(Id=execute_statement_response['Id']))[
            'Status'
        ] in ['PICKED', 'STARTED', 'SUBMITTED']:
            time.sleep(1)

        if describe_statement_response['Status'] == 'FAILED':
            raise Exception(describe_statement_response['Error'])

        log.info(f'Received response {describe_statement_response["Id"]}')
        return describe_statement_response['Id']

    def _execute_statement_return_records(self, sql: str):
        id = self._execute_statement(sql=sql)
        log.info(f'Returning records for sql {id=}...')
        try:
            response = self.client.get_statement_result(Id=id)
            next_token = response.get('NextToken', None)
            records = response.get('Records', [])
            while next_token:
                response = self.client.get_statement_result(Id=response['Id'], NextToken=next_token)
                new_records = response.get('Records', [])
                records.extend(new_records)
                next_token = response.get('NextToken', None)
            filtered_records = [[d for d in record if d.get('stringValue', False)] for record in records]
            log.info(f'Returning {len(filtered_records)} records from executed statement')
            return filtered_records
        except Exception as e:
            log.error(f'Failed to retrieve records for sql {id=}: {e}')
            raise e

    @staticmethod
    def double_quoted_name(name: str) -> str:
        return f'"{name}"'

    @staticmethod
    def single_quoted_name(name: str) -> str:
        return f"'{name}'"

    @staticmethod
    def quoted_object_names(*names) -> str:
        quoted_names = [RedshiftShareDataClient.double_quoted_name(name) for name in names if name]
        return '.'.join(quoted_names)

    def check_redshift_role_in_namespace(self, role) -> bool:
        """Check that a redshift role exists in database"""
        try:
            log.info(f'Checking {role=} exists...')
            sql_statement = 'SELECT role_name FROM SVV_ROLES;'
            records = self._execute_statement_return_records(sql=sql_statement)
            roles = [[d for d in record][0]['stringValue'] for record in records]
            log.info(f'Found {roles=}')
            return role in roles
        except Exception as e:
            log.error(f'Checking of {role=} failed due to: {e}')
            return False

    def create_datashare(self, datashare: str) -> bool:
        """Create datashare if not already created.
        Returns: bool: True if created, False if already exists
        """
        try:
            log.info(f'Creating {datashare=}...')
            sql_statement = f'CREATE DATASHARE {RedshiftShareDataClient.double_quoted_name(datashare)};'
            self._execute_statement(sql=sql_statement)
            return True
        except Exception as e:
            allowed_error_messages = [f'ERROR: share "{datashare}" already exists']
            error_message = e.args[0]
            if error_message in allowed_error_messages:
                log.info(f'Datashare {datashare} already exists')
                return False
            else:
                log.error(f'Creation of {datashare=} failed due to: {e}')
                raise e

    def drop_datashare(self, datashare: str):
        """
        Drop datashare if not already deleted
        """
        try:
            log.info(f'Dropping {datashare=}...')
            sql_statement = f'DROP DATASHARE {RedshiftShareDataClient.double_quoted_name(datashare)};'
            self._execute_statement(sql_statement)
        except Exception as e:
            allowed_error_message = f'ERROR: Datashare {datashare} does not exist'
            error_message = e.args[0]
            if error_message == allowed_error_message:
                log.info(f'Datashare {datashare} does not exist. No need to drop it any more.')
            else:
                log.error(f'Deletion of {datashare=} failed due to: {e}')
                raise e

    def check_datashare_exists(self, datashare: str):
        """Check that datashare exists by describing datashare"""
        try:
            log.info(f'Checking {datashare=}...')
            sql_statement = f'DESC DATASHARE {RedshiftShareDataClient.double_quoted_name(datashare)};'
            return self._execute_statement(sql=sql_statement)
        except Exception as e:
            log.error(f'Checking of {datashare=} failed due to: {e}')
            return False

    def add_schema_to_datashare(self, datashare: str, schema: str):
        """Add schema to datashare if not already added"""
        try:
            log.info(f'Adding schema {schema=} to {datashare=}...')
            sql_statement = f'ALTER DATASHARE {RedshiftShareDataClient.double_quoted_name(datashare)} ADD SCHEMA {RedshiftShareDataClient.double_quoted_name(schema)};'
            self._execute_statement(sql_statement)
        except Exception as e:
            allowed_error_message = f'ERROR: Schema {schema} is already added to the datashare {datashare}'
            error_message = e.args[0]
            if error_message == allowed_error_message:
                log.info(f'{schema=} is already present in {datashare=}')
            else:
                log.error(f'Adding {schema=} to {datashare=} failed due to: {e}')
                raise e

    def check_schema_in_datashare(self, datashare: str, schema: str) -> bool:
        """Check that schema exists in datashare by describing datashare"""
        try:
            log.info(f'Checking {schema=} in {datashare=}...')
            sql_statement = f'DESC DATASHARE {RedshiftShareDataClient.double_quoted_name(datashare)};'
            records = self._execute_statement_return_records(sql=sql_statement)
            schemas_in_datashare = [
                [d for d in record][5]['stringValue']
                for record in records
                if [d for d in record][4]['stringValue'] in ['schema']
            ]
            log.info(f'Found {schemas_in_datashare=}')
            return schema in schemas_in_datashare
        except Exception as e:
            log.error(f'Checking of {schema=} in {datashare=} failed due to: {e}')
            return False

    def add_table_to_datashare(self, datashare: str, schema: str, table_name: str):
        """Add table to datashare if not already added"""
        try:
            log.info(f'Adding table {table_name=} to {datashare=}...')
            table = RedshiftShareDataClient.quoted_object_names(self.database, schema, table_name)
            sql_statement = (
                f'ALTER DATASHARE {RedshiftShareDataClient.double_quoted_name(datashare)} ADD TABLE {table};'
            )
            self._execute_statement(sql_statement)
        except Exception as e:
            allowed_error_message = f'ERROR: Relation {table_name} is already added to the datashare {datashare}'
            error_message = e.args[0]
            if error_message == allowed_error_message:
                log.info(f'Table {table_name} is already present in the {datashare=}')
            else:
                log.error(f'Adding {table_name=} of {datashare=} failed due to: {e}')
                raise e

    def check_table_in_datashare(self, datashare: str, table_name: str) -> bool:
        """Check that table exists in datashare by describing datashare"""
        try:
            log.info(f'Checking {table_name=} in {datashare=}...')
            sql_statement = f'DESC DATASHARE {RedshiftShareDataClient.double_quoted_name(datashare)};'
            records = self._execute_statement_return_records(sql=sql_statement)
            tables_in_datashare = [
                [d for d in record][5]['stringValue'].split('.')[-1]  # "schemaname.tablename"
                for record in records
                if [d for d in record][4]['stringValue'] in ['table']
            ]
            log.info(f'Found {tables_in_datashare=}')
            return table_name in tables_in_datashare
        except Exception as e:
            log.error(f'Checking of {table_name} in {datashare=} failed due to: {e}')
            return False

    def remove_table_from_datashare(self, datashare: str, schema: str, table_name: str):
        """Remove table from datashare if not already removed"""
        try:
            log.info(f'Removing table {table_name=} from {datashare=}...')
            table = RedshiftShareDataClient.quoted_object_names(self.database, schema, table_name)
            sql_statement = (
                f'ALTER DATASHARE {RedshiftShareDataClient.double_quoted_name(datashare)} REMOVE TABLE {table};'
            )
            self._execute_statement(sql_statement)
        except Exception as e:
            allowed_error_message = f'ERROR: Datashare {datashare} does not contain the Relation {table_name}'
            error_message = e.args[0]
            if error_message == allowed_error_message:
                log.info(f'Table {table_name} does not exist on datashare {datashare}. No need to remove it any more.')
            else:
                log.error(f'Removing {table_name=} from {datashare=} failed due to: {e}')
                raise e

    def grant_datashare_usage_to_namespace(self, datashare: str, namespace: str):
        """Grant usage on datashare to cluster. If already granted, it succeeds"""
        try:
            log.info(f'Grant usage on {datashare=} to {namespace=}..')
            sql_statement = f'GRANT USAGE ON DATASHARE {RedshiftShareDataClient.double_quoted_name(datashare)} TO NAMESPACE {RedshiftShareDataClient.single_quoted_name(namespace)};'
            self._execute_statement(sql=sql_statement)
        except Exception as e:
            log.error(f'Granting usage to datashare failed due to: {e}')
            raise e

    def grant_datashare_usage_to_account(self, datashare: str, account: str):
        """Grant usage on datashare to AWS account. If already granted, it succeeds"""
        try:
            log.info(f'Grant usage on {datashare=} to {account=}..')
            sql_statement = f'GRANT USAGE ON DATASHARE {RedshiftShareDataClient.double_quoted_name(datashare)} TO ACCOUNT {RedshiftShareDataClient.single_quoted_name(account)};'
            self._execute_statement(sql=sql_statement)
        except Exception as e:
            log.error(f'Granting usage to datashare failed due to: {e}')
            raise e

    def check_consumer_permissions_to_datashare(self, datashare: str) -> bool:
        """Lists consumer datashares and checks it input datashare is among consumer datashares"""
        try:
            log.info(f'Check {datashare=} is accessible from target')
            sql_statement = 'SHOW DATASHARES;'
            records = self._execute_statement_return_records(sql=sql_statement)
            datashares_in_namespace = [[d for d in record][0]['stringValue'] for record in records]
            log.info(f'Found {datashares_in_namespace=}')
            return datashare in datashares_in_namespace
        except Exception as e:
            log.error(f'Checking of {datashare=} in consumer namespace failed due to: {e}')
            return False

    def create_database_from_datashare(self, database: str, datashare: str, namespace: str, account: str = None):
        """Create database from datashare. If it already exists, it succeeds"""
        try:
            log.info(f'Create {database=} from {datashare=} from source {namespace=}')
            if account:
                sql_statement = f'CREATE DATABASE {RedshiftShareDataClient.double_quoted_name(database)} WITH PERMISSIONS FROM DATASHARE {RedshiftShareDataClient.double_quoted_name(datashare)} OF ACCOUNT {RedshiftShareDataClient.single_quoted_name(account)} NAMESPACE {RedshiftShareDataClient.single_quoted_name(namespace)};'
            else:
                sql_statement = f'CREATE DATABASE {RedshiftShareDataClient.double_quoted_name(database)} WITH PERMISSIONS FROM DATASHARE {RedshiftShareDataClient.double_quoted_name(datashare)} OF NAMESPACE {RedshiftShareDataClient.single_quoted_name(namespace)};'
            self._execute_statement(sql=sql_statement)
        except Exception as e:
            allowed_error_message = (
                f'ERROR: database {RedshiftShareDataClient.double_quoted_name(database)} already exists'
            )
            error_message = e.args[0]
            if error_message == allowed_error_message:
                log.info(f'Database {RedshiftShareDataClient.double_quoted_name(database)} already exists')
            else:
                log.error(f'Creation of {database=} failed due to: {e}')
                raise e

    def drop_database(self, database: str):
        """Delete database, if not deleted already"""
        try:
            log.info(f'Dropping {database=}...')
            sql_statement = f'DROP DATABASE {RedshiftShareDataClient.double_quoted_name(database)};'
            self._execute_statement(sql=sql_statement)
        except Exception as e:
            allowed_error_message = (
                f'ERROR: database {RedshiftShareDataClient.double_quoted_name(database)} does not exist'
            )
            error_message = e.args[0]
            if error_message == allowed_error_message:
                log.info(
                    f'Database {RedshiftShareDataClient.double_quoted_name(database)} does not exist. No need to drop it any more.'
                )
            else:
                log.error(f'Dropping {database=} failed due to: {e}')
                raise e

    def check_database_exists(self, database: str) -> bool:
        """Check that database exists. List all databases in PG_DATABASE_INFO"""
        try:
            log.info(f'Checking {database=}...')
            sql_statement = 'SELECT * FROM PG_DATABASE_INFO'
            records = self._execute_statement_return_records(sql=sql_statement)
            databases_in_namespace = [[d for d in record][0]['stringValue'] for record in records]  # dataname
            log.info(f'Found {databases_in_namespace=}')
            return database in databases_in_namespace
        except Exception as e:
            log.error(f'Checking of {database=} failed due to: {e}')
            return False

    def grant_database_usage_access_to_redshift_role(self, database: str, rs_role: str):
        """Grant usage on database to a role. If already granted, it succeeds"""
        try:
            log.info(f'Grant usage on {database=} to Redshift role {rs_role=}..')
            sql_statement = f'GRANT USAGE ON DATABASE {RedshiftShareDataClient.double_quoted_name(database)} TO ROLE {RedshiftShareDataClient.double_quoted_name(rs_role)} ;'
            self._execute_statement(sql=sql_statement)
        except Exception as e:
            log.error(f'Granting usage to {database=} to {rs_role=} failed due to: {e}')
            raise e

    def revoke_database_usage_access_to_redshift_role(self, database: str, rs_role: str):
        """Revoke usage on database to a role. If already revoked, it succeeds"""
        try:
            log.info(f'Revoke usage on {database=} to Redshift role {rs_role=}..')
            sql_statement = f'REVOKE USAGE ON DATABASE {RedshiftShareDataClient.double_quoted_name(database)} FROM ROLE {RedshiftShareDataClient.double_quoted_name(rs_role)} ;'
            self._execute_statement(sql=sql_statement)
        except Exception as e:
            log.error(f'Revoking usage to {database=} to {rs_role=} failed due to: {e}')
            raise e

    def check_role_permissions_in_database(self, database: str, rs_role: str):
        """Check role permissions in database by querying SVV_DATABASE_PRIVILEGES"""
        try:
            log.info(f'Check if Redshift role {rs_role=} has usage permissions on {database=}..')
            sql_statement = f"SELECT database_name, privilege_type, identity_name, identity_type from SVV_DATABASE_PRIVILEGES where database_name={RedshiftShareDataClient.single_quoted_name(database)} and identity_name={RedshiftShareDataClient.single_quoted_name(rs_role)} and identity_type='role' and privilege_type='USAGE';"
            records = self._execute_statement_return_records(sql=sql_statement)
            return len(records) > 0
        except Exception as e:
            log.error(f'Checking of {rs_role=} usage permissions in {database=} failed due to: {e}')
            return False

    def create_external_schema(self, database: str, schema: str, external_schema: str):
        """Create external schema. If already exists, it succeeds"""
        try:
            log.info(f'Create external schema {external_schema=} in {database=}')
            sql_statement = f'CREATE EXTERNAL SCHEMA {RedshiftShareDataClient.double_quoted_name(external_schema)} FROM REDSHIFT DATABASE {RedshiftShareDataClient.double_quoted_name(database)} SCHEMA {RedshiftShareDataClient.double_quoted_name(schema)};'
            self._execute_statement(sql=sql_statement)
        except Exception as e:
            allowed_error_message = (
                f'ERROR: Schema {RedshiftShareDataClient.double_quoted_name(external_schema)} already exists'
            )
            error_message = e.args[0]
            if error_message == allowed_error_message:
                log.info(f'External schema {external_schema} already exists')
            else:
                log.error(f'Creation of external schema {external_schema=} in {database=} failed due to: {e}')
                raise e

    def drop_schema(self, schema: str):
        """Delete schema, if not deleted already"""
        try:
            log.info(f'Dropping {schema=}...')
            sql_statement = f'DROP SCHEMA {RedshiftShareDataClient.double_quoted_name(schema)};'
            self._execute_statement(sql=sql_statement)
        except Exception as e:
            allowed_error_message = f'ERROR: Schema {RedshiftShareDataClient.double_quoted_name(schema)} does not exist'
            error_message = e.args[0]
            if error_message == allowed_error_message:
                log.info(
                    f'Schema {RedshiftShareDataClient.double_quoted_name(schema)} does not exist. No need to drop it any more.'
                )
            else:
                log.error(f'Dropping {schema=} failed due to: {e}')
                raise e

    def check_schema_exists(self, schema: str, database: str) -> bool:
        """
        Check that schema exists. List schemas with SHOW SCHEMAS FROM DATABASE
        """
        try:
            log.info(f'Checking {schema=} exists...')
            sql_statement = f'SHOW SCHEMAS FROM DATABASE {RedshiftShareDataClient.double_quoted_name(database)};'
            records = self._execute_statement_return_records(sql=sql_statement)
            schemas_in_database = [[d for d in record][1]['stringValue'] for record in records]  # schema_name
            log.info(f'Found {schemas_in_database=}')
            return schema in schemas_in_database
        except Exception as e:
            log.error(f'Checking of {schema=} failed due to: {e}')
            return False

    def grant_schema_usage_access_to_redshift_role(self, schema: str, rs_role: str, database: str = None):
        """Grant usage on schema to a role. If already granted, it succeeds"""
        try:
            log.info(f'Grant usage on {database=} {schema=} to Redshift role {rs_role=}..')
            sql_statement = f'GRANT USAGE ON SCHEMA {RedshiftShareDataClient.quoted_object_names(database, schema)} TO ROLE {RedshiftShareDataClient.double_quoted_name(rs_role)};'
            self._execute_statement(sql=sql_statement)
        except Exception as e:
            log.error(f'Granting usage to {schema=} to {rs_role=} failed due to: {e}')
            raise e

    def revoke_schema_usage_access_to_redshift_role(self, schema: str, rs_role: str):
        """Revoke usage on schema to a role. If already granted, it succeeds"""
        try:
            log.info(f'Revoke usage on {schema=} to Redshift role {rs_role=}..')
            sql_statement = f'REVOKE USAGE ON SCHEMA {RedshiftShareDataClient.double_quoted_name(schema)} FROM ROLE {RedshiftShareDataClient.double_quoted_name(rs_role)};'
            self._execute_statement(sql=sql_statement)
        except Exception as e:
            log.error(f'Revoking usage to {schema=} to {rs_role=} failed due to: {e}')
            raise e

    def check_role_permissions_in_schema(self, schema: str, rs_role: str):
        """Check role permissions in schema. List permissions by querying SVV_SCHEMA_PRIVILEGES"""
        try:
            sql_statement = f"SELECT namespace_name, privilege_type, identity_name, identity_type from SVV_SCHEMA_PRIVILEGES where namespace_name={RedshiftShareDataClient.single_quoted_name(schema)} and identity_name={RedshiftShareDataClient.single_quoted_name(rs_role)} and identity_type='role' and privilege_type='USAGE';"
            records = self._execute_statement_return_records(sql=sql_statement)
            return len(records) > 0
        except Exception as e:
            log.error(f'Checking of {rs_role=} usage permissions in {schema=} failed due to: {e}')
            return False

    def grant_select_table_access_to_redshift_role(self, schema: str, table: str, rs_role: str, database: str = None):
        """
        Grant select on table to a role. If already granted, it succeeds
        GRANT SELECT ON local_db.schema.table;
        GRANT SELECT ON external_schema.table;
        """
        try:
            log.info(f'Grant select on {table=} from {schema=} and {database=} to Redshift role {rs_role=}..')
            sql_statement = f'GRANT SELECT ON {RedshiftShareDataClient.quoted_object_names(database, schema, table)} TO ROLE {RedshiftShareDataClient.double_quoted_name(rs_role)};'
            self._execute_statement(sql=sql_statement)
        except Exception as e:
            log.error(f'Granting select to {table=} from {schema=} and {database=} to {rs_role=} failed due to: {e}')
            raise e

    def revoke_select_table_access_to_redshift_role(self, schema: str, table: str, rs_role: str, database: str = None):
        """
        Revoke select on table to a role. If table is deleted, it succeeds
        REVOKE SELECT ON local_db.schema.table;
        REVOKE SELECT ON external_schema.table;
        """
        try:
            log.info(f'Revoke select on {table=} from {schema=} and {database=} to Redshift role {rs_role=}..')
            sql_statement = f'REVOKE SELECT ON {RedshiftShareDataClient.quoted_object_names(database, schema, table)} FROM ROLE {RedshiftShareDataClient.double_quoted_name(rs_role)};'
            self._execute_statement(sql=sql_statement)
        except Exception as e:
            allowed_error_message = f'ERROR: Object {RedshiftShareDataClient.double_quoted_name(table)} does not exist'
            error_message = e.args[0]
            if error_message == allowed_error_message:
                log.info(f'{table=} does not exists, no permissions can be revoked')
            else:
                log.error(
                    f'Revoking select to {table=} from {schema=} and {database=} to {rs_role=} failed due to: {e}'
                )
                raise e


def redshift_share_data_client(account_id: str, region: str, connection: RedshiftConnection) -> RedshiftShareDataClient:
    "Factory of Client"
    return RedshiftShareDataClient(account_id=account_id, region=region, connection=connection)
