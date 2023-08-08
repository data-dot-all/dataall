from typing import List
from aws_cdk import aws_iam as iam

from dataall.core.environment.cdk.env_role_core_policies.data_policy import S3Policy
from dataall.modules.dataset_sharing.aws.kms_client import KmsClient
from dataall.modules.datasets_base.db.dataset_repository import DatasetRepository
from dataall.modules.datasets_base.db.models import Dataset


class DatasetS3Policy(S3Policy):

    def get_statements(self, session):
        datasets = DatasetRepository.list_group_datasets(
            session,
            environment_id=self.environment.environmentUri,
            group_uri=self.team.groupUri,
        )
        return DatasetS3Policy._generate_dataset_statements(datasets)

    @staticmethod
    def _generate_dataset_statements(datasets: List[Dataset]):
        allowed_buckets = []
        allowed_access_points = []
        statements = []
        if datasets:
            dataset: Dataset
            for dataset in datasets:
                allowed_buckets.append(f'arn:aws:s3:::{dataset.S3BucketName}')
                allowed_access_points.append(
                    f'arn:aws:s3:{dataset.region}:{dataset.AwsAccountId}:accesspoint/{dataset.datasetUri}*')
            allowed_buckets_content = [f"{bucket}/*" for bucket in allowed_buckets]
            statements = [
                iam.PolicyStatement(
                    sid="ListDatasetsBuckets",
                    actions=[
                        "s3:ListBucket",
                        "s3:GetBucketLocation"
                    ],
                    resources=allowed_buckets,
                    effect=iam.Effect.ALLOW,
                ),
                iam.PolicyStatement(
                    sid="ReadWriteDatasetsBuckets",
                    actions=[
                        "s3:PutObject",
                        "s3:PutObjectAcl",
                        "s3:GetObject",
                        "s3:GetObjectAcl",
                        "s3:GetObjectVersion",
                        "s3:DeleteObject"
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=allowed_buckets_content,
                ),
                iam.PolicyStatement(
                    sid="ReadAccessPointsDatasetBucket",
                    actions=[
                        's3:GetAccessPoint',
                        's3:GetAccessPointPolicy',
                        's3:GetAccessPointPolicyStatus',
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=allowed_access_points,
                ),
            ]
            kms_statement = DatasetS3Policy._set_allowed_kms_keys_statements(datasets)
            if kms_statement:
                statements.append(kms_statement)
        return statements

    @staticmethod
    def _set_allowed_kms_keys_statements(datasets):
        allowed_buckets_kms_keys = []
        if datasets:
            dataset: Dataset
            for dataset in datasets:
                if dataset.imported and dataset.importedKmsKey:
                    key_id = KmsClient(dataset.AwsAccountId, dataset.region).get_key_id(
                        key_alias=f"alias/{dataset.KmsAlias}"
                    )
                    if key_id:
                        allowed_buckets_kms_keys.append(
                            f"arn:aws:kms:{dataset.region}:{dataset.AwsAccountId}:key/{key_id}")
            if len(allowed_buckets_kms_keys):
                return iam.PolicyStatement(
                    sid="KMSImportedDatasetAccess",
                    actions=[
                        "kms:Decrypt",
                        "kms:Encrypt",
                        "kms:ReEncrypt*",
                        "kms:DescribeKey",
                        "kms:GenerateDataKey"
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=allowed_buckets_kms_keys
                )
        return None
