import logging

from dataall.aws.handlers.sts import SessionHelper
from dataall.modules.omics.db.models import OmicsProject
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class OmicsClient:
    """
    A Omics projects proxy client that is used to send requests to AWS
    """

    def __init__(self, omics: OmicsProject):
        session = SessionHelper.remote_session(omics.AWSAccountId)
        self._client = session.client('omics', region_name=omics.region)

#TODO: Implement boto3 client for Omics
def client(notebook: SagemakerNotebook) -> OmicsClient: # replace notebook and Sagemaker Notebook 
    """Factory method to retrieve the client to send request to AWS"""
    return OmicsClient(notebook)
