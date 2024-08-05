import logging

from botocore.exceptions import ClientError

from dataall.base.aws.sts import SessionHelper

log = logging.getLogger(__name__)


class RedshiftClient:
    def __init__(self, account_id: str, region: str) -> None:
        session = SessionHelper.remote_session(accountid=account_id, region=region)
        self.client = session.client(service_name='redshift', region_name=region)

    def describe_cluster(self, clusterId: str):
        log.info(f'Describing cluster {clusterId=}')
        return self.client.describe_clusters(ClusterIdentifier=clusterId)['Clusters'][0]

    def get_cluster_namespaceId(self, clusterId: str):
        log.info(f'Describing cluster {clusterId=}')
        return self.client.describe_clusters(ClusterIdentifier=clusterId)['Clusters'][0]['ClusterNamespaceArn'].split(
            ':'
        )[-1]


def redshift_client(account_id: str, region: str) -> RedshiftClient:
    "Factory of Client"
    return RedshiftClient(account_id=account_id, region=region)
