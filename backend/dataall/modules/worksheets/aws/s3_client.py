import boto3
from botocore.config import Config

from botocore.exceptions import ClientError
import logging
from dataall.base.db.exceptions import AWSResourceNotFound
from dataall.base.aws.sts import SessionHelper

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dataall.core.environment.db.environment_models import Environment
    try:
        from mypy_boto3_s3 import S3Client as S3ClientType
    except ImportError:
        S3ClientType = None

log = logging.getLogger(__name__)


class S3Client:

    def __init__(self, env: 'Environment'):
        self._client = SessionHelper.remote_session(env.AwsAccountId, env.region).client('s3', region_name=env.region)
        self._env = env

    @property
    def client(self) -> 'S3ClientType':
        return self._client

    def get_presigned_url(self, bucket, key, expire_minutes: int = 15):
        expire_seconds = expire_minutes * 60
        try:
            presigned_url = self.client.generate_presigned_url(
                'get_object',
                Params=dict(
                    Bucket=bucket,
                    Key=key,
                ),
                ExpiresIn=expire_seconds,
            )
            return presigned_url
        except ClientError as e:
            log.error(f'Failed to get presigned URL due to: {e}')
            raise e

    def object_exists(self, bucket, key) -> bool:
        try:
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                log.info(f'Object {key} not found in bucket {bucket}')
                return False
            log.error(f'Failed to check object existence due to: {e}')
            raise AWSResourceNotFound('s3_object_exists', f'Object {key} not found in bucket {bucket}')


    def put_object(self, bucket, key, body):
        try:
            self.client.put_object(Bucket=bucket, Key=key, Body=body)
        except ClientError as e:
            log.error(f'Failed to put object due to: {e}')
            raise e


    def get_object(self, bucket, key) -> str:
        try:
            response = self.client.get_object(Bucket=bucket, Key=key)
            return response['Body'].read().decode('utf-8')
        except ClientError as e:
            log.error(f'Failed to get object due to: {e}')
            raise e
