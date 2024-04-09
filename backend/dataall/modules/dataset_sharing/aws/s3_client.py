import logging

from dataall.base.aws.sts import SessionHelper
from botocore.exceptions import ClientError

import json

log = logging.getLogger(__name__)


class S3ControlClient:
    def __init__(self, account_id: str, region: str):
        session = SessionHelper.remote_session(accountid=account_id)
        self._client = session.client('s3control', region_name=region)
        self._account_id = account_id

    def get_bucket_access_point_arn(self, access_point_name: str):
        try:
            access_point = self._client.get_access_point(
                AccountId=self._account_id,
                Name=access_point_name,
            )
        except Exception as e:
            log.info(f'Failed to get S3 bucket access point {access_point_name} on {self._account_id} : {e}')
            return None
        else:
            return access_point['AccessPointArn']

    def create_bucket_access_point(self, bucket_name: str, access_point_name: str):
        try:
            access_point = self._client.create_access_point(
                AccountId=self._account_id,
                Name=access_point_name,
                Bucket=bucket_name,
            )
        except Exception as e:
            log.error(f'S3 bucket access point creation failed for location {bucket_name} : {e}')
            raise e
        else:
            return access_point['AccessPointArn']

    def delete_bucket_access_point(self, access_point_name: str):
        try:
            self._client.delete_access_point(
                AccountId=self._account_id,
                Name=access_point_name,
            )
        except Exception as e:
            log.error(f'Failed to delete S3 bucket access point {access_point_name}/{self._account_id} : {e}')
            raise e

    def get_access_point_policy(self, access_point_name: str):
        try:
            response = self._client.get_access_point_policy(
                AccountId=self._account_id,
                Name=access_point_name,
            )
        except Exception as e:
            log.info(f'Failed to get policy of access point {access_point_name} on {self._account_id} : {e}')
            return None
        else:
            return response['Policy']

    def attach_access_point_policy(self, access_point_name: str, policy: str):
        try:
            self._client.put_access_point_policy(AccountId=self._account_id, Name=access_point_name, Policy=policy)
        except Exception as e:
            log.error(f'S3 bucket access point policy creation failed : {e}')
            raise e

    @staticmethod
    def generate_access_point_policy_template(
        principal_id: str,
        access_point_arn: str,
        s3_prefix: str,
    ):
        policy = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Sid': f'{principal_id}0',
                    'Effect': 'Allow',
                    'Principal': {'AWS': '*'},
                    'Action': 's3:ListBucket',
                    'Resource': f'{access_point_arn}',
                    'Condition': {'StringLike': {'s3:prefix': [f'{s3_prefix}/*'], 'aws:userId': [f'{principal_id}:*']}},
                },
                {
                    'Sid': f'{principal_id}1',
                    'Effect': 'Allow',
                    'Principal': {'AWS': '*'},
                    'Action': 's3:GetObject',
                    'Resource': [f'{access_point_arn}/object/{s3_prefix}/*'],
                    'Condition': {'StringLike': {'aws:userId': [f'{principal_id}:*']}},
                },
            ],
        }
        return policy

    @staticmethod
    def generate_default_bucket_policy(s3_bucket_name: str):
        policy = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Effect': 'Deny',
                    'Principal': {'AWS': '*'},
                    'Sid': 'RequiredSecureTransport',
                    'Action': 's3:*',
                    'Resource': [f'arn:aws:s3:::{s3_bucket_name}', f'arn:aws:s3:::{s3_bucket_name}/*'],
                    'Condition': {'Bool': {'aws:SecureTransport': 'false'}},
                },
            ],
        }
        return policy


class S3Client:
    def __init__(self, account_id, region):
        session = SessionHelper.remote_session(accountid=account_id)
        self._client = session.client('s3', region_name=region)
        self._account_id = account_id

    def create_bucket_policy(self, bucket_name: str, policy: str):
        try:
            s3cli = self._client
            s3cli.put_bucket_policy(
                Bucket=bucket_name,
                Policy=policy,
                ConfirmRemoveSelfBucketAccess=False,
                ExpectedBucketOwner=self._account_id,
            )
            log.info(f'Created bucket policy of {bucket_name} on {self._account_id} successfully')
        except ClientError as e:
            if e.response['Error']['Code'] == 'MalformedPolicy':
                log.info('MalformedPolicy. Lets try again')
                bucket_policy = json.loads(policy)
                statements = bucket_policy['Statement']
                for statement in statements:
                    if 'DataAll-Bucket' in statement['Sid']:
                        principal_list = statement['Principal']['AWS']
                        if isinstance(principal_list, str):
                            principal_list = [principal_list]
                        new_principal_list = principal_list[:]
                        for p_id in principal_list:
                            if "AROA" in p_id:
                                new_principal_list.remove(p_id)
                        statement['Principal']['AWS'] = new_principal_list
                bucket_policy['Statement'] = statements
                log.info(f'New Policy: {json.dumps(bucket_policy)}')
                self.create_bucket_policy(bucket_name, json.dumps(bucket_policy))
        except Exception as e:
            log.error(f'Bucket policy created failed on bucket {bucket_name} of {self._account_id} : {e}')
            raise e

    def get_bucket_policy(self, bucket_name: str):
        try:
            s3cli = self._client
            response = s3cli.get_bucket_policy(Bucket=bucket_name, ExpectedBucketOwner=self._account_id)
        except Exception as e:
            log.warning(f'Failed to get bucket policy of {bucket_name} : {e}')
            return None
        else:
            return response['Policy']
