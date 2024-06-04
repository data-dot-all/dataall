import logging
from botocore.exceptions import ClientError

from dataall.base.aws.sts import SessionHelper

log = logging.getLogger(__name__)


class LakeFormation:
    def __init__(self, account_id: str, region: str) -> None:
        session = SessionHelper.remote_session(accountid=account_id, region=region)
        self.client = session.client(service_name='lakeformation', region_name=region)

    def register_resource_datashare(self, datashare_arn: str) -> None:
        try:
            log.info(f'Registering resource {datashare_arn}')
            self.client.response = self.client.register_resource(ResourceArn=datashare_arn)
        except ClientError as e:
            log.error(e)
            raise e
