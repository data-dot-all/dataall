import logging

from botocore.exceptions import ClientError

from dataall.base.aws.sts import SessionHelper
from dataall.modules.redshift_datasets.services.redshift_enums import DatashareStatus

log = logging.getLogger(__name__)


class Redshift:
    def __init__(self, account_id: str, region: str) -> None:
        session = SessionHelper.remote_session(accountid=account_id, region=region)
        self.client = session.client(service_name='redshift', region_name=region)

    def describe_cluster(self, clusterId: str):
        try:
            log.info(f'Describing cluster {clusterId=}')
            return self.client.describe_clusters(ClusterIdentifier=clusterId)['Clusters'][0]
        except ClientError as e:
            log.error(e)
            raise e


def redshift_client(account_id: str, region: str) -> Redshift:
    """Factory method to retrieve the client to send request to AWS"""
    return Redshift(account_id, region)
