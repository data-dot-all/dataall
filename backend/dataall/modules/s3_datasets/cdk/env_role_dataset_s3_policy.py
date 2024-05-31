from typing import List
from aws_cdk import aws_iam as iam

from dataall.core.environment.cdk.env_role_core_policies.data_policy import S3Policy
from dataall.modules.s3_datasets.db.dataset_repositories import DatasetRepository
from dataall.modules.s3_datasets.db.dataset_models import S3Dataset


class DatasetS3Policy(S3Policy):
    def get_statements(self, session):
        datasets = DatasetRepository.list_group_datasets(
            session,
            environment_id=self.environment.environmentUri,
            group_uri=self.team.groupUri,
        )
        return DatasetS3Policy._generate_dataset_statements(datasets)

    @staticmethod
    def _generate_dataset_statements(datasets: List[S3Dataset]):
        allowed_buckets = []
        allowed_access_points = []
        statements = []
        if datasets:
            dataset: S3Dataset
            for dataset in datasets:
                allowed_buckets.append(f'arn:aws:s3:::{dataset.S3BucketName}')
                allowed_access_points.append(
                    f'arn:aws:s3:{dataset.region}:{dataset.AwsAccountId}:accesspoint/{dataset.datasetUri}*'
                )
            allowed_buckets_content = [f'{bucket}/*' for bucket in allowed_buckets]
            statements = [
                iam.PolicyStatement(
                    sid='ListDatasetsBuckets',
                    actions=['s3:ListBucket', 's3:GetBucketLocation'],
                    resources=allowed_buckets,
                    effect=iam.Effect.ALLOW,
                ),
                iam.PolicyStatement(
                    sid='ReadWriteDatasetsBuckets',
                    actions=[
                        's3:PutObject',
                        's3:PutObjectAcl',
                        's3:GetObject',
                        's3:GetObjectAcl',
                        's3:GetObjectVersion',
                        's3:DeleteObject',
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=allowed_buckets_content,
                ),
                iam.PolicyStatement(
                    sid='ReadAccessPointsDatasetBucket',
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
        imported_kms_alias = []
        if datasets:
            # Datasets belonging to a team and an environment are present in same region and aws account
            imported_dataset_resources = [f'arn:aws:kms:{datasets[0].region}:{datasets[0].AwsAccountId}:key/*']
            dataset: S3Dataset
            for dataset in datasets:
                if dataset.imported and dataset.importedKmsKey:
                    imported_kms_alias.append(f'alias/{dataset.KmsAlias}')

            if len(imported_kms_alias):
                return iam.PolicyStatement(
                    sid='KMSImportedDatasetAccess',
                    actions=['kms:Decrypt', 'kms:Encrypt', 'kms:ReEncrypt*', 'kms:DescribeKey', 'kms:GenerateDataKey'],
                    effect=iam.Effect.ALLOW,
                    resources=imported_dataset_resources,
                    conditions={'ForAnyValue:StringLike': {'kms:ResourceAliases': imported_kms_alias}},
                )
        return None
