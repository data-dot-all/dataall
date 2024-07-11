import logging

from botocore.exceptions import ClientError

from dataall.base.aws.sts import SessionHelper


log = logging.getLogger(__name__)


class Redshift:
    def __init__(self, account_id: str, region: str) -> None:
        session = SessionHelper.remote_session(accountid=account_id, region=region)
        self.client = session.client(service_name='redshift', region_name=region)

    def authorize_datashare_to_catalog(self, datashare_arn: str, account: str) -> None:
        try:
            log.info(f'Authorizing datashare {datashare_arn=} to consumer DataCatalog/{account}')
            self.client.authorize_data_share(
                DataShareArn=datashare_arn, ConsumerIdentifier=f'DataCatalog/{account}', AllowWrites=False
            )
        except ClientError as e:
            log.error(e)
            raise e

    def associate_data_share_catalog(self, datashare_arn: str, account: str, region: str):
        try:
            log.info(f'Associating datashare {datashare_arn=} to consumer DataCatalog/{account}')
            self.client.associate_data_share_consumer(
                DataShareArn=datashare_arn, ConsumerArn=f'arn:aws:glue:{region}:{account}:catalog', AllowWrites=False
            )
        except ClientError as e:
            log.error(e)
            raise e

    def describe_datashare_status(self, datashare_arn: str):
        try:
            log.info(f'Checking status of datashare {datashare_arn=}')
            response = self.client.describe_data_shares(DataShareArn=datashare_arn)
            return response.get('DataShares', [])[0].get('DataShareAssociations', [])[0].get('Status')
        except ClientError as e:
            log.error(e)
            return 'NotFound'
