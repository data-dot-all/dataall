import logging
import json

from dataall.base.aws.sts import SessionHelper
from botocore.exceptions import ClientError

log = logging.getLogger(__name__)

DATAALL_BUCKET_KMS_DECRYPT_SID = 'DataAll-Bucket-KMS-Decrypt'
DATAALL_KMS_PIVOT_ROLE_PERMISSIONS_SID = 'KMSPivotRolePermissions'
DATAALL_ACCESS_POINT_KMS_DECRYPT_SID = 'DataAll-Access-Point-KMS-Decrypt'


def _remove_malformed_principal(policy: str):
    log.info(f'Malformed Policy: {policy}')
    kms_policy = json.loads(policy)
    statements = kms_policy['Statement']
    for statement in statements:
        if statement.get('Sid', 'no-sid') in [
            DATAALL_BUCKET_KMS_DECRYPT_SID,
            DATAALL_KMS_PIVOT_ROLE_PERMISSIONS_SID,
            DATAALL_ACCESS_POINT_KMS_DECRYPT_SID,
        ]:
            principal_list = statement['Principal']['AWS']
            if isinstance(principal_list, str):
                principal_list = [principal_list]
            new_principal_list = principal_list[:]
            for p_id in principal_list:
                if 'AROA' in p_id:
                    new_principal_list.remove(p_id)
            statement['Principal']['AWS'] = new_principal_list
    kms_policy['Statement'] = statements
    log.info(f'Fixed Policy: {json.dumps(kms_policy)}')
    return json.dumps(kms_policy)


class KmsClient:
    _DEFAULT_POLICY_NAME = 'default'

    def __init__(self, account_id: str, region: str):
        session = SessionHelper.remote_session(accountid=account_id)
        self._client = session.client('kms', region_name=region)
        self._account_id = account_id

    def put_key_policy(self, key_id: str, policy: str, second_try=True):
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
                if second_try:
                    log.info('MalformedPolicy. Lets try again')
                    fixed_policy = _remove_malformed_principal(policy)
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
