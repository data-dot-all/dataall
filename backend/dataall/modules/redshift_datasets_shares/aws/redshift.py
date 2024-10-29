import logging

from botocore.exceptions import ClientError

from dataall.base.aws.sts import SessionHelper
from dataall.modules.redshift_datasets_shares.services.redshift_shares_enums import RedshiftDatashareStatus

log = logging.getLogger(__name__)


class RedshiftShareClient:
    def __init__(self, account_id: str, region: str) -> None:
        session = SessionHelper.remote_session(accountid=account_id, region=region)
        self.client = session.client(service_name='redshift', region_name=region)

    def authorize_datashare(self, datashare_arn: str, account: str) -> None:
        """
        Authorize a datashare to an account. If the datashare is already authorized it will succeed.
        """
        try:
            log.info(f'Authorizing datashare {datashare_arn=} to consumer {account}...')
            self.client.authorize_data_share(
                DataShareArn=datashare_arn, ConsumerIdentifier=account
            )  # AllowWrites in preview
        except ClientError as e:
            log.error(e)
            raise e

    def associate_datashare(self, datashare_arn: str, consumer_arn: str):
        """
        Associate a datashare with a namespace. If the datashare is already associated it will succeed.
        """
        try:
            log.info(f'Associating datashare {datashare_arn=} to {consumer_arn=}...')
            self.client.associate_data_share_consumer(
                DataShareArn=datashare_arn, ConsumerArn=consumer_arn, AssociateEntireAccount=False
            )  # AllowWrites in preview
        except ClientError as e:
            log.error(e)
            raise e

    def get_datashare_status(self, datashare_arn: str, consumer_id: str):
        try:
            log.info(f'Checking status of datashare {datashare_arn=} for {consumer_id=}')
            response = self.client.describe_data_shares(DataShareArn=datashare_arn)
            all_datashares = response.get('DataShares', [])
            if not all_datashares:
                return RedshiftDatashareStatus.NotFound.value
            consumer_datashares = [
                d.get('Status')
                for d in all_datashares[0].get('DataShareAssociations', [])
                if d.get('ConsumerIdentifier') == consumer_id
            ]
            return next(iter(consumer_datashares), RedshiftDatashareStatus.NotFound.value)
        except ClientError as e:
            log.error(e)
            return RedshiftDatashareStatus.NotFound.value


def redshift_share_client(account_id: str, region: str) -> RedshiftShareClient:
    "Factory of Client"
    return RedshiftShareClient(account_id=account_id, region=region)
