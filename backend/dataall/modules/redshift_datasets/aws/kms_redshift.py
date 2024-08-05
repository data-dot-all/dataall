import logging

from dataall.base.aws.sts import SessionHelper
from botocore.exceptions import ClientError


log = logging.getLogger(__name__)


class KmsClient:
    def __init__(self, account_id: str, region: str):
        session = SessionHelper.remote_session(accountid=account_id, region=region)
        self._client = session.client('kms', region_name=region)
        self._account_id = account_id
        self.region = region

    def describe_kms_key(self, key_id: str):
        # The same client function is defined in the data_sharing module. Duplication is allowed to avoid coupling.
        try:
            response = self._client.describe_key(
                KeyId=key_id,
            )
            log.info(f'KMS key used to encrypt cluster {response=}')
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDenied':
                raise Exception(
                    f'Data.all Environment Pivot Role does not have kms:DescribeKey Permission for key {key_id}: {e}'
                )
            log.error(f'Failed to describe key {key_id}: {e}')
            return None
        else:
            return response['KeyMetadata']


def kms_redshift_client(account_id: str, region: str) -> KmsClient:
    "Factory of Client"
    return KmsClient(account_id=account_id, region=region)
