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
        # session = SessionHelper.remote_session(awsAccountId,'arn:aws:iam::545117064741:role/dataallPivotRole')
        session = SessionHelper.remote_session(awsAccountId,'arn:aws:iam::290341535759:role/OmicsCallsPatrickRole')
        self._client = session.client('omics')
        
    #TODO: Implement boto3 client calls for Omics
        
    def get_workflow(self, id: str):
        try:
            response = self._client.get_workflow(id=id,
                type='READY2RUN'
            )
            return response
        except ClientError as e:
            logger.error(
                f'Could not retrieve Ready2Run Omics Workflows status due to: {e} '
            )
            return 'ERROR LISTING WORKFLOWS'

    def get_workflow_run(self, id: str):
        try:
            response = self._client.get_run(id=id
            )
            return response
        except ClientError as e:
            logger.error(
                f'Could not retrieve workflow run status due to: {e} '
            )
            return 'ERROR GETTING WORKFLOW RUN'    
        

    def run_omics_workflow(self, workflowId: str, workflowType: str, roleArn: str, parameters: str):
        try:
            response = self._client.start_run(workflowId, workflowType, roleArn, parameters
            )
            return response
        except ClientError as e:
            logger.error(
                f'Could not retrieve workflow run status due to: {e} '
            )
            return 'ERROR RUNNING OMICS WORKFLOW'           
        

    
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
