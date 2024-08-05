import logging
import time
from botocore.exceptions import ClientError
from dataall.base.aws.sts import SessionHelper
from dataall.modules.redshift_datasets.db.redshift_models import RedshiftConnection

log = logging.getLogger(__name__)


class RedshiftDataClient:
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
        return f'{RedshiftDataClient.identifier(self.database)}.{RedshiftDataClient.identifier(schema)}.{RedshiftDataClient.identifier(table_name)}'

    def get_redshift_connection_database(self):
        databases = []
        try:
            log.info(f'Looking for {self.database} in databases...')

            list_databases_response = self.client.list_databases(**self.execute_connection_params)
            if 'Databases' in list_databases_response.keys():
                databases = list_databases_response['Databases']
            log.info(f'Returning {databases=}...')
            return databases
        except ClientError as e:
            log.error(e)
            raise e

    def list_redshift_schemas(self):
        schemas = []
        try:
            log.info(f'Fetching {self.database} schemas')
            list_schemas_response = self.client.list_schemas(**self.execute_connection_params)
            if 'Schemas' in list_schemas_response.keys():
                schemas = list_schemas_response['Schemas']

            # Remove "internal" schemas
            if 'information_schema' in schemas:
                schemas.remove('information_schema')
            if 'pg_catalog' in schemas:
                schemas.remove('pg_catalog')
            log.info(f'Returning {schemas=}...')
            return schemas
        except ClientError as e:
            log.error(e)
            raise e

    def list_redshift_tables(self, schema: str):
        tables_list = []
        try:
            log.info(f'Fetching {self.database} tables')
            list_tables_response = self.client.list_tables(
                **self.execute_connection_params, SchemaPattern=schema, MaxResults=1000
            )
            next_token = list_tables_response.get('NextToken', None)
            if 'Tables' in list_tables_response.keys():
                tables_list = list_tables_response['Tables']
                while next_token:
                    list_tables_response = self.client.list_tables(
                        **self.execute_connection_params, NextToken=next_token, MaxResults=1000, SchemaPattern=schema
                    )
                    if 'Tables' in list_tables_response.keys():
                        tables_list.extend(list_tables_response['Tables'])
                    next_token = list_tables_response.get('NextToken', None)

            tables = [
                {'name': table['name'], 'type': table['type']}
                for table in tables_list
                if table['type'] in ['TABLE', 'VIEW']
            ]
            log.info(f'Returning {tables=}...')
            return tables
        except ClientError as e:
            log.error(e)
            raise e

    def list_redshift_table_columns(self, schema: str, table: str):
        columns_list = []
        try:
            log.info(f'Fetching {self.database} tables')
            response = self.client.describe_table(
                **self.execute_connection_params, Schema=schema, Table=table, MaxResults=1000
            )
            next_token = response.get('NextToken', None)
            if 'ColumnList' in response.keys():
                columns_list = response['ColumnList']
                while next_token:
                    response = self.client.describe_table(
                        **self.execute_connection_params,
                        Schema=schema,
                        Table=table,
                        MaxResults=1000,
                        NextToken=next_token,
                    )
                    if 'ColumnList' in response.keys():
                        columns_list.extend(response['ColumnList'])
                    next_token = response.get('NextToken', None)
            for col in columns_list:
                col['nullable'] = True if col['nullable'] == 1 else False
            log.info(f'Returning {columns_list=}')
            return columns_list
        except ClientError as e:
            log.error(e)
            raise e


def redshift_data_client(account_id: str, region: str, connection: RedshiftConnection) -> RedshiftDataClient:
    "Factory of Client"
    return RedshiftDataClient(account_id=account_id, region=region, connection=connection)
