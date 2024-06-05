import logging
import time

from typing import List
from botocore.exceptions import ClientError

from dataall.base.aws.sts import SessionHelper
from dataall.modules.redshift_datasets.db.redshift_models import RedshiftConnection


log = logging.getLogger(__name__)


class Redshift:
    def __init__(self, account_id: str, region: str) -> None:
        session = SessionHelper.remote_session(accountid=account_id, region=region)
        self.client = session.client(service_name='redshift', region_name=region)

    def authorize_catalog_datashare(self, datashare_arn: str, account: str) -> None:
        try:
            log.info(f'Authorizing datashare {datashare_arn=} to consumer DataCatalog/{account}')
            self.client.authorize_data_share(
                DataShareArn=datashare_arn, ConsumerIdentifier=f'DataCatalog/{account}', AllowWrites=False
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
            raise e
