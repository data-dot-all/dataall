import logging
import boto3

from dataall.base.aws.sts import SessionHelper
from dataall.modules.omics.db.models import OmicsRun
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class OmicsClient:
    """
    An Omics proxy client that is used to send requests to AWS
    """

    def __init__(self, awsAccountId: str):
        session = SessionHelper.remote_session(awsAccountId,'arn:aws:iam::545117064741:role/dataallPivotRole')
        self._client = session.client('omics')
        
    #TODO: Implement boto3 client calls for Omics
        
    def list_workflows(self) -> list:
        try:
            response = self._client.list_workflows(
                type='READY2RUN',
                maxResults=100 
            )
            # items = response.get('items', 'ERROR LISTING WORKFLOWS')
            return response.get('items', 'ERROR LISTING WORKFLOWS')
        except ClientError as e:
            logger.error(
                f'Could not retrieve Ready2Run Omics Workflows status due to: {e} '
            )
            return 'ERROR LISTING WORKFLOWS'

def client(run: OmicsRun) -> OmicsClient:
    """Factory method to retrieve the client to send request to AWS"""
    return OmicsClient(run)
