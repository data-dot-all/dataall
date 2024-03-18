import logging
import time

from dataall.base.aws.sts import SessionHelper
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_client(AwsAccountId, region):
    session = SessionHelper.remote_session(AwsAccountId)
    return session.client('redshift-data', region_name=region)


class RedshiftDataClient:
    """A Redshift client that is used to send requests to AWS"""

    def __init__(self, AwsAccountId, region):
        self._client = get_client(AwsAccountId=AwsAccountId, region=region)

    def execute_statement(
        self, database: str, sql: str, cluster: str = None, workgroup: str = None, secret: str = None
    ):
        """Wrapper around redshiftData execute_statement() API
        which also checks the result of the execution

        Args:
            database (str): Name of the database where the command is executed
            sql (str): SQL command which will be executed
            workgroup (str): Name of the workgroup if using Redshift Serverless
            cluster (str): Name of the cluster if using Redshift cluster
            secret (srt): ARN of the secret that enables access to the database. This parameter is required when authenticating using Secrets Manager.

        Raises:
            Exception: In case there occurs an error in the SQL statement execution
        """
        if workgroup:
            execute_statement_response = self._client.execute_statement(
                Database=database, WorkgroupName=workgroup, Sql=sql, SecretArn=secret
            )
        elif cluster:
            execute_statement_response = self._client.execute_statement(
                Database=database, ClusterIdentifier=cluster, Sql=sql, SecretArn=secret
            )
        else:
            raise Exception('Cluster or  workgroup must be provided')

        execution_finished = False
        while not execution_finished:
            describe_statement_response = self._client.describe_statement(Id=execute_statement_response['Id'])
            time.sleep(1)
            execution_finished = describe_statement_response['Status'] not in ['PICKED', 'STARTED', 'SUBMITTED']

        if describe_statement_response['Status'] == 'FAILED':
            raise Exception(describe_statement_response['Error'])

        logger.info(f'Received response from describe_statement(): {describe_statement_response}')
        return describe_statement_response['Id']


def redshift_client(AwsAccountId, region) -> RedshiftDataClient:
    """Factory method to retrieve the client to send request to AWS"""
    return RedshiftDataClient(AwsAccountId, region)
