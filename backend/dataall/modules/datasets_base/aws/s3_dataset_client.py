import json
import logging

from botocore.config import Config
from botocore.exceptions import ClientError

from dataall.base.aws.sts import SessionHelper
from dataall.modules.datasets_base.db.dataset_models import Dataset

log = logging.getLogger(__name__)


class S3DatasetClient:

    def __init__(self, dataset: Dataset):
        """
        It first starts a session assuming the pivot role,
        then we define another session assuming the dataset role from the pivot role
        """
        pivot_role_session = SessionHelper.remote_session(accountid=dataset.AwsAccountId)
        session = SessionHelper.get_session(base_session=pivot_role_session, role_arn=dataset.IAMDatasetAdminRoleArn)
        self._client = session.client(
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

    def get_bucket_encryption(self) -> (str, str):
        dataset = self._dataset
        try:
            response = self._client.get_bucket_encryption(
                Bucket=dataset.S3BucketName,
                ExpectedBucketOwner=dataset.AwsAccountId
            )
            rule = response['ServerSideEncryptionConfiguration']['Rules'][0]
            encryption = rule['ApplyServerSideEncryptionByDefault']
            s3_encryption = encryption['SSEAlgorithm']
            kms_id = encryption.get('KMSMasterKeyID')
            return s3_encryption, kms_id
        except ClientError as e:
            log.error(f'Cannot fetch the bucket encryption configuration for {dataset.S3BucketName}')
            return None, None
