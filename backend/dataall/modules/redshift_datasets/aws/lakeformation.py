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
            self.client.register_resource(ResourceArn=datashare_arn)
        except ClientError as e:
            log.error(e)
            if e.response['Error']['Code'] == 'AlreadyExistsException':
                log.debug(f'Resource already registered {datashare_arn}')
            else:
                raise e

    def get_registered_resource_datashare(self, datashare_arn: str) -> None:
        try:
            log.info(f'Getting registered resource {datashare_arn}')
            response = self.client.describe_resource(ResourceArn=datashare_arn)
            return response.get('ResourceInfo', None)
        except ClientError as e:
            log.error(e)
            raise e
