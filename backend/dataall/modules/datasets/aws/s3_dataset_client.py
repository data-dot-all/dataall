import json

from botocore.config import Config
from botocore.exceptions import ClientError

from dataall.aws.handlers.sts import SessionHelper
from dataall.modules.datasets_base.db.models import Dataset


class S3DatasetClient:

    def __init__(self, dataset: Dataset):
        self._client = SessionHelper.remote_session(dataset.AwsAccountId).client(
            's3',
            region_name=dataset.region,
            config=Config(signature_version='s3v4', s3={'addressing_style': 'virtual'}),
        )
        self._dataset = dataset

    def get_file_upload_presigned_url(self, data):
        dataset = self._dataset
        try:
            self._client.get_bucket_acl(
                Bucket=dataset.S3BucketName, ExpectedBucketOwner=dataset.AwsAccountId
            )
            response = self._client.generate_presigned_post(
                Bucket=dataset.S3BucketName,
                Key=data.get('prefix', 'uploads') + '/' + data.get('fileName'),
                ExpiresIn=15 * 60,
            )

            return json.dumps(response)
        except ClientError as e:
            raise e
