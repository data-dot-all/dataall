import json
import logging

from botocore.config import Config
from botocore.exceptions import ClientError

from dataall.base.aws.sts import SessionHelper
from dataall.modules.datasets_base.db.dataset_models import Dataset

log = logging.getLogger(__name__)


class S3DatasetClient:

    def __init__(self, dataset: Dataset):
        self._client = SessionHelper.remote_session(accountid=dataset.AwsAccountId, role=dataset.IAMDatasetAdminRoleArn).client(
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


class S3DatasetBucketPolicyClient:
    def __init__(self, dataset: Dataset):
        session = SessionHelper.remote_session(accountid=dataset.AwsAccountId)
        self._client = session.client('s3')
        self._dataset = dataset

    def get_bucket_policy(self):
        dataset = self._dataset
        try:
            policy = self._client.get_bucket_policy(Bucket=dataset.S3BucketName)['Policy']
            log.info(f'Current bucket policy---->:{policy}')
            policy = json.loads(policy)
        except ClientError as err:
            if err.response['Error']['Code'] == 'NoSuchBucketPolicy':
                log.info(f"No policy attached to '{dataset.S3BucketName}'")

            elif err.response['Error']['Code'] == 'NoSuchBucket':
                log.error(f'Bucket deleted {dataset.S3BucketName}')

            elif err.response['Error']['Code'] == 'AccessDenied':
                log.error(
                    f'Access denied in {dataset.AwsAccountId} '
                    f'(s3:{err.operation_name}, '
                    f"resource='{dataset.S3BucketName}')"
                )
            else:
                log.exception(
                    f"Failed to get '{dataset.S3BucketName}' policy in {dataset.AwsAccountId}"
                )
            policy = {
                'Version': '2012-10-17',
                'Statement': [
                    {
                        'Sid': 'OwnerAccount',
                        'Effect': 'Allow',
                        'Action': ['s3:*'],
                        'Resource': [
                            f'arn:aws:s3:::{dataset.S3BucketName}',
                            f'arn:aws:s3:::{dataset.S3BucketName}/*',
                        ],
                        'Principal': {
                            'AWS': f'arn:aws:iam::{dataset.AwsAccountId}:root'
                        },
                    }
                ],
            }

        return policy

    def put_bucket_policy(self, policy):
        dataset = self._dataset
        update_policy_report = {
            'datasetUri': dataset.datasetUri,
            'bucketName': dataset.S3BucketName,
            'accountId': dataset.AwsAccountId,
        }
        try:
            policy_json = json.dumps(policy) if isinstance(policy, dict) else policy
            log.info(
                f"Putting new bucket policy on '{dataset.S3BucketName}' policy {policy_json}"
            )
            response = self._client.put_bucket_policy(
                Bucket=dataset.S3BucketName, Policy=policy_json
            )
            log.info(f'Bucket Policy updated: {response}')
            update_policy_report.update({'status': 'SUCCEEDED'})
        except ClientError as e:
            log.error(
                f'Failed to update bucket policy '
                f"on '{dataset.S3BucketName}' policy {policy} "
                f'due to {e} '
            )
            update_policy_report.update({'status': 'FAILED'})

        return update_policy_report
