import logging

from dataall.base.aws.sts import SessionHelper
from botocore.exceptions import ClientError


log = logging.getLogger(__name__)


class KmsClient:
    _DEFAULT_POLICY_NAME = 'default'

    def __init__(self, account_id: str, region: str):
        session = SessionHelper.remote_session(accountid=account_id, region=region)
        self._client = session.client('kms', region_name=region)
        self._account_id = account_id
        self.region = region

    def get_key_id(self, key_alias: str):
        # The same client function is defined in the data_sharing module. Duplication is allowed to avoid coupling.
        try:
            response = self._client.describe_key(
                KeyId=key_alias,
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDenied':
                raise Exception(
                    f'Data.all Environment Pivot Role does not have kms:DescribeKey Permission for key {key_alias}: {e}'
                )
            log.error(f'Failed to get kms key id of {key_alias}: {e}')
            return None
        else:
            return response['KeyMetadata']['KeyId']

    def check_key_exists(self, key_alias: str):
        try:
            key_exist = False
            paginator = self._client.get_paginator('list_aliases')
            for page in paginator.paginate():
                key_aliases = [alias['AliasName'] for alias in page['Aliases']]
                if key_alias in key_aliases:
                    key_exist = True
                    break
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDenied':
                raise Exception(
                    f'Data.all Environment Pivot Role does not have kms:ListAliases Permission in account {self._account_id}: {e}'
                )
            log.error(f'Failed to list KMS key aliases in account {self._account_id}: {e}')
            return None
        else:
            return key_exist
