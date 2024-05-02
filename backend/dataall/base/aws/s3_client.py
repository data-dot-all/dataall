import boto3
from botocore.config import Config

from botocore.exceptions import ClientError
import logging

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
