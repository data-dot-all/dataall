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

        execution_finished = False
        describe_statement_response = None
        while not execution_finished:
            describe_statement_response = self.client.describe_statement(Id=execute_statement_response['Id'])
            time.sleep(1)
            execution_finished = describe_statement_response['Status'] not in ['PICKED', 'STARTED', 'SUBMITTED']

        if describe_statement_response['Status'] == 'FAILED':
            raise Exception(describe_statement_response['Error'])

        log.info(f'Received response {describe_statement_response=}')
        return describe_statement_response['Id']

    @staticmethod
    def identifier(name: str) -> str:
        return f'"{name}"'

    def fully_qualified_table_name(self, schema: str, table_name: str) -> str:
        return f'{RedshiftShareDataClient.identifier(self.database)}.{RedshiftShareDataClient.identifier(schema)}.{RedshiftShareDataClient.identifier(table_name)}'

    def create_datashare(self, datashare: str):
        """
        Create datashare if not already created
        """
        try:
            log.info(f'Creating {datashare=}...')
            sql_statement = f'CREATE DATASHARE {RedshiftShareDataClient.identifier(datashare)};'
            self._execute_statement(sql=sql_statement)

        except Exception as e:
            allowed_error_messages = [f'ERROR: share "{datashare}" already exists']
            error_message = e.args[0]
            if error_message in allowed_error_messages:
                log.info(f'Datashare {datashare} already exists')
            else:
                raise e

    def drop_datashare(self, database: str, workgroup: str, datashare: str):
        sql_statement = f'DROP DATASHARE {RedshiftShareDataClient.identifier(datashare)};'
        try:
            self._execute_statement(database, workgroup, sql_statement)
        except Exception as e:
            allowed_error_message = f'ERROR: Datashare {datashare} does not exist'
            error_message = e.args[0]
            if error_message == allowed_error_message:
                log.info(f'Datashare {datashare} does not exist. No need to drop it any more.')
            else:
                raise e

    # def describe_datashare(self, datashare: str):
    #     """
    #     Describe datashare
    #     """
    #     log.info(f'Describing {datashare=}...')
    #     sql_statement = f'DESC DATASHARE {RedshiftShareDataClient.identifier(datashare)};'
    #     # we need to transform the output
    #     return self._execute_statement(sql=sql_statement)

    def add_schema_to_datashare(self, datashare: str, schema: str):
        """
        Add schema to datashare if not already added
        """
        log.info(f'Adding schema {schema=} to {datashare=}...')
        sql_statement = f'ALTER DATASHARE {RedshiftShareDataClient.identifier(datashare)} ADD SCHEMA {RedshiftShareDataClient.identifier(schema)};'
        try:
            self._execute_statement(sql_statement)
        except Exception as e:
            allowed_error_message = f'ERROR: Schema {schema} is already added to the datashare {datashare}'
            error_message = e.args[0]
            if error_message == allowed_error_message:
                log.info(f'{schema=} is already present in {datashare=}')
            else:
                raise e

    def add_table_to_datashare(self, datashare: str, schema: str, table_name: str):
        """
        Add table to datashare if not already added
        """
        log.info(f'Adding table {table_name=} to {datashare=}...')
        fq_table_name = self.fully_qualified_table_name(schema, table_name)
        sql_statement = f'ALTER DATASHARE {RedshiftShareDataClient.identifier(datashare)} ADD TABLE {fq_table_name};'
        try:
            self._execute_statement(sql_statement)
        except Exception as e:
            allowed_error_message = f'ERROR: Relation {table_name} is already added to the datashare {datashare}'
            error_message = e.args[0]
            if error_message == allowed_error_message:
                log.info(f'Table {fq_table_name} is already present in the {datashare=}')
            else:
                raise e

    def remove_table_from_datashare(self, schema: str, database: str, workgroup: str, datashare: str, table_name: str):
        fq_table_name = self.fully_qualified_table_name(database, schema, table_name)
        sql_statement = f'ALTER DATASHARE {RedshiftShareDataClient.identifier(datashare)} REMOVE TABLE {fq_table_name};'
        try:
            self._execute_statement(database, workgroup, sql_statement)
        except Exception as e:
            allowed_error_message = f'ERROR: Datashare {datashare} does not contain the Relation {table_name}'
            error_message = e.args[0]
            if error_message == allowed_error_message:
                log.info(
                    f'Table {fq_table_name} does not exist on datashare {datashare}. No need to remove it any more.'
                )
            else:
                raise e

    def grant_usage_to_datashare(self, datashare: str, namespace: str):
        """
        Grant usage on datashare to cluster. If already granted, it succeeds
        """
        log.info(f'Grant usage on {datashare=} to {namespace=}..')
        sql_statement = (
            f"GRANT USAGE ON DATASHARE {RedshiftShareDataClient.identifier(datashare)} TO NAMESPACE'{namespace}';"
        )
        self._execute_statement(sql=sql_statement)

    def create_database_from_datashare(self, database: str, datashare: str, namespace: str):
        log.info(f'Create {database=} from {datashare=} from source {namespace=}')
        sql_statement = f"CREATE DATABASE {RedshiftShareDataClient.identifier(database)} FROM DATASHARE {RedshiftShareDataClient.identifier(datashare)} OF NAMESPACE'{namespace}';"
        try:
            self._execute_statement(sql=sql_statement)
        except Exception as e:
            allowed_error_message = f'ERROR: database {RedshiftShareDataClient.identifier(database)} already exists'
            error_message = e.args[0]
            if error_message == allowed_error_message:
                log.info(f'Database {RedshiftShareDataClient.identifier(database)} already exists')
            else:
                raise e

    def drop_database(self, database: str):
        log.info(f'DROP {database=}')
        sql_statement = f"DROP DATABASE {RedshiftShareDataClient.identifier(database)}';"
        try:
            self._execute_statement(sql=sql_statement)
        except Exception as e:
            allowed_error_message = f'ERROR: database {RedshiftShareDataClient.identifier(database)} does not exist'
            error_message = e.args[0]
            if error_message == allowed_error_message:
                log.info(
                    f'Database {RedshiftShareDataClient.identifier(database)} does not exist. No need to drop it any more.'
                )
            else:
                raise e

    def create_external_schema(self, database: str, schema: str):
        log.info(f'Create external schema {schema=} in {database=}')
        external_schema = RedshiftShareDataClient.identifier(f'{database}_{schema}')
        sql_statement = f'CREATE EXTERNAL SCHEMA {external_schema} FROM DATABASE {RedshiftShareDataClient.identifier(database)} SCHEMA {RedshiftShareDataClient.identifier(schema)};'
        try:
            self._execute_statement(sql=sql_statement)
        except Exception as e:
            allowed_error_message = f'ERROR: Schema {external_schema} already exists'
            error_message = e.args[0]
            if error_message == allowed_error_message:
                log.info(f'External schema {external_schema} already exists')
            else:
                raise e

    def grant_schema_usage_access_to_redshift_role(self, schema: str, rs_role: str):
        """
        Grant usage on schema to a role. If already granted, it succeeds
        """
        log.info(f'Grant usage on {schema=} to Redshift role {rs_role=}..')
        sql_statement = f"GRANT USAGE ON SCHEMA {RedshiftShareDataClient.identifier(schema)} TO '{rs_role}';"
        self._execute_statement(sql=sql_statement)

    def grant_select_table_access_to_redshift_role(self, schema: str, table: str, rs_role: str):
        """
        Grant select on table to a role. If already granted, it succeeds
        """
        log.info(f'Grant select on {table=} from {schema=} to Redshift role {rs_role=}..')
        sql_statement = (
            f"GRANT SELECT ON TABLE {RedshiftShareDataClient.fully_qualified_table_name(schema, table)} TO '{rs_role}';"
        )
        self._execute_statement(sql=sql_statement)

    def revoke_select_table_access_to_redshift_role(self, schema: str, table: str, rs_role: str):
        """
        Revoke select on table to a role. If already revoked, it succeeds
        """
        log.info(f'Grant select on {table=} from {schema=} to Redshift role {rs_role=}..')
        sql_statement = f"REVOKE SELECT ON TABLE {RedshiftShareDataClient.fully_qualified_table_name(schema, table)} TO '{rs_role}';"
        self._execute_statement(sql=sql_statement)


def redshift_share_data_client(account_id: str, region: str, connection: RedshiftConnection) -> RedshiftShareDataClient:
    "Factory of Client"
    return RedshiftShareDataClient(account_id=account_id, region=region, connection=connection)
