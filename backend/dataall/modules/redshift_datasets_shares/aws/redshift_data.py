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


def redshift_data_client(account_id: str, region: str, connection: RedshiftConnection) -> RedshiftDataClient:
    "Factory of Client"
    return RedshiftDataClient(account_id=account_id, region=region, connection=connection)
