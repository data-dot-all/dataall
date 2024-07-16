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

    def authorize_datashare_to_catalog(self, datashare_arn: str, account: str) -> None:
        """
        Authorize a datashare to a DataCatalog account.
        If the datashare is already authorized it will succeed.
        """
        try:
            log.info(f'Authorizing datashare {datashare_arn=} to consumer DataCatalog/{account}')
            self.client.authorize_data_share(
                DataShareArn=datashare_arn, ConsumerIdentifier=f'DataCatalog/{account}', AllowWrites=False
            )
        except ClientError as e:
            log.error(e)
            raise e

    def associate_data_share_catalog(self, datashare_arn: str, account: str, region: str):
        """
        Associate a datashare with a DataCatalog account.
        If the datashare is already associated it will succeed.
        """
        try:
            log.info(f'Associating datashare {datashare_arn=} to consumer DataCatalog/{account}')
            self.client.associate_data_share_consumer(
                DataShareArn=datashare_arn, ConsumerArn=f'arn:aws:glue:{region}:{account}:catalog', AllowWrites=False
            )
        except ClientError as e:
            log.error(e)
            raise e

    def get_datashare_status(self, datashare_arn: str, consumer_id: str):
        try:
            log.info(f'Checking status of datashare {datashare_arn=}')
            response = self.client.describe_data_shares(DataShareArn=datashare_arn)
            datashares_for_consumer = [d for d in response.get('DataShares', [])[0].get('DataShareAssociations', []) if d.get('ConsumerIdentifier') == consumer_id]
            return datashares_for_consumer[0].get('Status') if len(datashares_for_consumer) > 0 else DatashareStatus.NotFound.value
        except ClientError as e:
            log.error(e)
            return DatashareStatus.NotFound.value
