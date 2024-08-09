import logging

from dataall.base.aws.sts import SessionHelper
from botocore.exceptions import ClientError
from dataall.modules.s3_datasets_shares.aws.share_policy_verifier import SharePolicyVerifier

log = logging.getLogger(__name__)

DATAALL_BUCKET_KMS_DECRYPT_SID = 'DataAll-Bucket-KMS-Decrypt'
DATAALL_BUCKET_KMS_ENCRYPT_SID = 'DataAll-Bucket-KMS-Encrypt'
DATAALL_KMS_PIVOT_ROLE_PERMISSIONS_SID = 'KMSPivotRolePermissions'
DATAALL_ACCESS_POINT_KMS_DECRYPT_SID = 'DataAll-Access-Point-KMS-Decrypt'
DATAALL_ACCESS_POINT_KMS_ENCRYPT_SID = 'DataAll-Access-Point-KMS-Encrypt'

DATAALL_KMS_SIDS = [
    DATAALL_BUCKET_KMS_DECRYPT_SID,
    DATAALL_BUCKET_KMS_ENCRYPT_SID,
    DATAALL_KMS_PIVOT_ROLE_PERMISSIONS_SID,
    DATAALL_ACCESS_POINT_KMS_DECRYPT_SID,
    DATAALL_ACCESS_POINT_KMS_ENCRYPT_SID,
]


class KmsClient:
    _DEFAULT_POLICY_NAME = 'default'

    def __init__(self, account_id: str, region: str):
        session = SessionHelper.remote_session(accountid=account_id, region=region)
        self._client = session.client('kms', region_name=region)
        self._account_id = account_id
        self.region = region

    def put_key_policy(self, key_id: str, policy: str, fix_malformed_principals=True):
        try:
            self._client.put_key_policy(
                KeyId=key_id,
                PolicyName=self._DEFAULT_POLICY_NAME,
                Policy=policy,
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDenied':
                raise Exception(
                    f'Data.all Environment Pivot Role does not have kms:PutKeyPolicy Permission for key id {key_id}: {e}'
                )
            elif e.response['Error']['Code'] == 'MalformedPolicyDocumentException':
                if fix_malformed_principals:
                    log.info('MalformedPolicy. Lets try again')
                    fixed_policy = SharePolicyVerifier.remove_malformed_principal(
                        policy, DATAALL_KMS_SIDS, self._account_id, self.region
                    )
                    self.put_key_policy(key_id, fixed_policy, False)
                    return
            log.error(f'Failed to attach policy to KMS key {key_id} on {self._account_id}: {e} ')
            raise e

    def get_key_policy(self, key_id: str):
        try:
            response = self._client.get_key_policy(
                KeyId=key_id,
                PolicyName=self._DEFAULT_POLICY_NAME,
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDenied':
                raise Exception(
                    f'Data.all Environment Pivot Role does not have kms:GetKeyPolicy Permission for key id {key_id}: {e}'
                )
            log.error(f'Failed to get kms key policy of key {key_id}: {e}')
            return None
        else:
            return response['Policy']

    def get_key_id(self, key_alias: str):
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
