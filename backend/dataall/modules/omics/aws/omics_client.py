import logging

from dataall.aws.handlers.sts import SessionHelper
from dataall.modules.omics.db.models import OmicsRun
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class OmicsClient:
    """
    An Omics proxy client that is used to send requests to AWS
    """

    def __init__(self, run: OmicsRun):
        session = SessionHelper.remote_session(run.AWSAccountId)
        self._client = session.client('omics', region_name=run.region)

#TODO: Implement boto3 client for Omics
def client(run: OmicsRun) -> OmicsClient:
    """Factory method to retrieve the client to send request to AWS"""
    return OmicsClient(run)
