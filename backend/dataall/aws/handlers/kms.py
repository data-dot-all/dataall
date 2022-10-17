import logging

from .sts import SessionHelper

log = logging.getLogger(__name__)


class KMS:

    @staticmethod
    def client(account_id: str):
        session = SessionHelper.remote_session(accountid=account_id)
        return session.client('kms')

    @staticmethod
    def put_key_policy(
        account_id: str,
        key_id: str,
        policy_name: str,
        policy: str,
    ):
        try:
            kms_client = KMS.client(account_id)
            kms_client.put_key_policy(
                KeyId=key_id,
                PolicyName=policy_name,
                Policy=policy,
            )
        except Exception as e:
            log.error(
                f'Failed to attach policy to KMS key {key_id} on {account_id} : {e} '
            )
            raise e

    @staticmethod
    def get_key_policy(
        account_id: str,
        key_id: str,
        policy_name: str,
    ):
        try:
            kms_client = KMS.client(account_id)
            response = kms_client.get_key_policy(
                KeyId=key_id,
                PolicyName=policy_name,
            )
        except Exception as e:
            log.error(
                f'Failed to get kms key policy of key {key_id} : {e}'
            )
            return None
        else:
            return response['Policy']

    @staticmethod
    def get_key_id(
        account_id: str,
        key_alias: str,
    ):
        try:
            kms_client = KMS.client(account_id)
            response = kms_client.describe_key(
                KeyId=key_alias,
            )
        except Exception as e:
            log.error(
                f'Failed to get kms key id of {key_alias} : {e}'
            )
            return None
        else:
            return response['KeyMetadata']['KeyId']
