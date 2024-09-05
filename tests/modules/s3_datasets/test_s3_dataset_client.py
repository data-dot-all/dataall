from unittest.mock import MagicMock, patch

import pytest
from assertpy import assert_that

from dataall.modules.s3_datasets.aws.s3_dataset_client import S3DatasetClient
from dataall.modules.s3_datasets.db.dataset_models import S3Dataset


@patch('dataall.modules.s3_datasets.aws.s3_dataset_client.SessionHelper', autospec=True)
@pytest.mark.parametrize(
    'bucket_encryption,expected',
    [
        (
            {
                'ServerSideEncryptionConfiguration': {
                    'Rules': [
                        {
                            'ApplyServerSideEncryptionByDefault': {
                                'SSEAlgorithm': 'aws:kms',
                                'KMSMasterKeyID': 'arn:aws:kms:us-east-1:999999999999:alias/keyalias',
                            },
                            'BucketKeyEnabled': True,
                        }
                    ]
                }
            },
            ('aws:kms', 'alias', 'keyalias'),
        ),
        (
            {
                'ServerSideEncryptionConfiguration': {
                    'Rules': [
                        {
                            'ApplyServerSideEncryptionByDefault': {
                                'SSEAlgorithm': 'aws:kms',
                                'KMSMasterKeyID': 'arn:aws:kms:us-east-1:999999999999:key/123',
                            },
                            'BucketKeyEnabled': True,
                        }
                    ]
                }
            },
            ('aws:kms', 'key', '123'),
        ),
        (
            {
                'ServerSideEncryptionConfiguration': {
                    'Rules': [
                        {'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'AES256'}, 'BucketKeyEnabled': True}
                    ]
                }
            },
            ('AES256', None, None),
        ),
    ],
)
def test_get_bucket_encryption(session_helper, bucket_encryption, expected):
    session_helper.remote_session.return_value.client.return_value.get_bucket_encryption.return_value = (
        bucket_encryption
    )
    dataset = MagicMock(spec=S3Dataset)
    client = S3DatasetClient(dataset)
    assert_that(client.get_bucket_encryption()).is_equal_to(expected)
