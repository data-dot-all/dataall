import logging

from dataall.base.aws.sts import SessionHelper
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_client(AwsAccountId, region):
    session = SessionHelper.remote_session(AwsAccountId)
    return session.client('redshift-serverless', region_name=region)


class RedshiftServerlessClient:
    """A Redshift client that is used to send requests to AWS"""

    def __init__(self, AwsAccountId, region):
        self._client = get_client(AwsAccountId=AwsAccountId, region=region)

    def get_namespace(self, namespace_name):
        try:
            response = self._client.get_namespace(namespaceName=namespace_name)
            return response['namespace']
        except ClientError as e:
            raise Exception(f'Cannot find cluster {namespace_name}: {e}')


def redshift_serverless_client(AwsAccountId, region) -> RedshiftServerlessClient:
    """Factory method to retrieve the client to send request to AWS"""
    return RedshiftServerlessClient(AwsAccountId, region)
