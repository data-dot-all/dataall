import json
from unittest.mock import MagicMock

import pytest

from dataall.base.db.exceptions import RequiredParameter, InvalidInput, UnauthorizedOperation, AWSResourceNotFound
from dataall.modules.s3_datasets.services.dataset_service import DatasetService
from dataall.modules.s3_datasets.db.dataset_models import S3Dataset


def test_s3_managed_bucket_import(mock_aws_client, api_context_1):
    dataset = S3Dataset(KmsAlias=None)

    mock_encryption_bucket(mock_aws_client, 'AES256', None)

    assert DatasetService._check_imported_resources(dataset)


def test_s3_managed_bucket_but_bucket_encrypted_with_kms(mock_aws_client, api_context_1):
    dataset = S3Dataset(KmsAlias=None)

    mock_encryption_bucket(mock_aws_client, 'aws:kms', 'any')
    with pytest.raises(RequiredParameter):
        DatasetService._check_imported_resources(dataset)


def test_s3_managed_bucket_but_alias_provided(mock_aws_client, api_context_1):
    dataset = S3Dataset(KmsAlias='Key')

    mock_encryption_bucket(mock_aws_client, 'AES256', None)
    with pytest.raises(InvalidInput):
        DatasetService._check_imported_resources(dataset)


def test_kms_encrypted_bucket_but_key_not_exist(mock_aws_client, api_context_1):
    alias = 'alias'
    dataset = S3Dataset(KmsAlias=alias)
    mock_encryption_bucket(mock_aws_client, 'aws:kms', 'any')
    mock_existing_alias(mock_aws_client)

    with pytest.raises(AWSResourceNotFound):
        DatasetService._check_imported_resources(dataset)


def test_kms_encrypted_bucket_but_key_is_wrong(mock_aws_client, api_context_1):
    alias = 'key_alias'
    kms_id = 'kms_id'
    dataset = S3Dataset(KmsAlias=alias)
    mock_encryption_bucket(mock_aws_client, 'aws:kms', 'wrong')
    mock_existing_alias(mock_aws_client, f'alias/{alias}')
    mock_key_id(mock_aws_client, kms_id)

    with pytest.raises(InvalidInput):
        DatasetService._check_imported_resources(dataset)


def test_kms_encrypted_bucket_imported(mock_aws_client, api_context_1):
    alias = 'key_alias'
    kms_id = 'kms_id'
    dataset = S3Dataset(KmsAlias=alias)
    mock_encryption_bucket(mock_aws_client, 'aws:kms', kms_id)
    mock_existing_alias(mock_aws_client, f'alias/{alias}')
    mock_key_id(mock_aws_client, kms_id)

    assert DatasetService._check_imported_resources(dataset)


def mock_encryption_bucket(mock_aws_client, algorithm, kms_id=None):
    response = f"""
            {{
                "ServerSideEncryptionConfiguration": {{
                    "Rules": [
                        {{
                            "ApplyServerSideEncryptionByDefault": {{
                                "SSEAlgorithm": "{algorithm}",
                                "KMSMasterKeyID": "{kms_id}"
                            }},
                            "BucketKeyEnabled": true
                        }}
                    ]
                }}
            }}
        """
    mock_aws_client.get_bucket_encryption.return_value = json.loads(response)


def mock_existing_alias(mock_aws_client, existing_alias='unknown'):
    paginator = MagicMock()
    mock_aws_client.get_paginator.return_value = paginator
    response = f"""
        {{
            "Aliases":  [ {{
                "AliasName": "{existing_alias}"
            }} ] 
        }}
    """
    paginator.paginate.return_value = [json.loads(response)]


def mock_key_id(mock_aws_client, key_id):
    response = f"""
        {{
            "KeyMetadata": {{
                "KeyId": "{key_id}"
            }}
        }}
    """
    mock_aws_client.describe_key.return_value = json.loads(response)
