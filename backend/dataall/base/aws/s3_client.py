import boto3
from botocore.config import Config

from botocore.exceptions import ClientError
import logging
from dataall.base.db.exceptions import AWSResourceNotFound

log = logging.getLogger(__name__)


class S3_client:
    @staticmethod
    def client(region: str, config):
        if config is None:
            config = Config(signature_version='s3v4', s3={'addressing_style': 'virtual'})
        return boto3.client(
            's3',
            region_name=region,
            config=config,
        )

    @staticmethod
    def get_presigned_url(region, bucket, key, expire_minutes: int = 15):
        try:
            presigned_url = S3_client.client(region, None).generate_presigned_url(
                'get_object',
                Params=dict(
                    Bucket=bucket,
                    Key=key,
                ),
                ExpiresIn=expire_minutes * 60,
            )
            return presigned_url
        except ClientError as e:
            log.error(f'Failed to get presigned URL due to: {e}')
            raise e

    @staticmethod
    def object_exists(region, bucket, key) -> bool:
        try:
            S3_client.client(region, None).head_object(Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            log.error(f'Failed to check object existence due to: {e}')
            if e.response['Error']['Code'] == '404':
                return False
            raise AWSResourceNotFound('s3_object_exists', f'Object {key} not found in bucket {bucket}')

    @staticmethod
    def put_object(region, bucket, key, body):
        try:
            S3_client.client(region, None).put_object(Bucket=bucket, Key=key, Body=body)
        except ClientError as e:
            log.error(f'Failed to put object due to: {e}')
            raise e

    @staticmethod
    def get_object(region, bucket, key):
        try:
            response = S3_client.client(region, None).get_object(Bucket=bucket, Key=key)
            return response['Body'].read().decode('utf-8')
        except ClientError as e:
            log.error(f'Failed to get object due to: {e}')
            raise e
