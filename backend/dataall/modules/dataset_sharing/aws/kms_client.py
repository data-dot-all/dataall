import logging

from dataall.base.aws.sts import SessionHelper

log = logging.getLogger(__name__)


class KmsClient:
    _DEFAULT_POLICY_NAME = "default"

    def __init__(self, account_id: str, region: str):
        session = SessionHelper.remote_session(accountid=account_id)
        self._client = session.client('kms', region_name=region)
        self._account_id = account_id

    def put_key_policy(self, key_id: str, policy: str):
        try:
            self._client.put_key_policy(
                KeyId=key_id,
                PolicyName=self._DEFAULT_POLICY_NAME,
                Policy=policy,
            )
        except Exception as e:
            log.error(
                f'Failed to attach policy to KMS key {key_id} on {self._account_id} : {e} '
            )
            raise e

    def get_key_policy(self, key_id: str):
        try:
            response = self._client.get_key_policy(
                KeyId=key_id,
                PolicyName=self._DEFAULT_POLICY_NAME,
            )
        except Exception as e:
            log.error(
                f'Failed to get kms key policy of key {key_id} : {e}'
            )
            return None
        else:
            return response['Policy']

    def get_key_id(self, key_alias: str):
        try:
            response = self._client.describe_key(
                KeyId=key_alias,
            )
        except Exception as e:
            log.error(
                f'Failed to get kms key id of {key_alias} : {e}'
            )
            return None
        else:
            return response['KeyMetadata']['KeyId']

    def check_key_exists(self, key_alias: str):
        try:
            key_exist = False
            paginator = self._client.get_paginator('list_aliases')
            for page in paginator.paginate():
                key_aliases = [alias["AliasName"] for alias in page['Aliases']]
                if key_alias in key_aliases:
                    key_exist = True
                    break
        except Exception as e:
            log.error(
                f'Failed to list kms key aliases in account {self._account_id}: {e}'
            )
            return None
        else:
            return key_exist
