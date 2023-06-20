import logging

from dataall.aws.handlers.sts import SessionHelper
from dataall.modules.omics.db.models import OmicsPipeline
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class OmicsClient:
    """
    An Omics proxy client that is used to send requests to AWS
    """

    def __init__(self, pipeline: OmicsProject):
        session = SessionHelper.remote_session(pipeline.AWSAccountId)
        self._client = session.client('omics', region_name=pipeline.region)

#TODO: Implement boto3 client for Omics
def client(pipeline: OmicsPipeline) -> OmicsClient:
    """Factory method to retrieve the client to send request to AWS"""
    return OmicsClient(pipeline)
