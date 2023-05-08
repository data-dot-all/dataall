from typing import List
from aws_cdk import aws_iam as iam

from dataall.cdkproxy.stacks.policies.data_policy import DataPolicy
from dataall.modules.datasets_base.db.models import Dataset
from dataall.modules.datasets.db.dataset_service import DatasetService


class DatasetDataPolicy(DataPolicy):

    def get_statements(self, session):
        datasets = DatasetService.list_group_datasets(
            session,
            environment_id=self.environment.environmentUri,
            group_uri=self.team.groupUri,
        )
        return DatasetDataPolicy._generate_dataset_statements(datasets)

    @staticmethod
    def _generate_dataset_statements(datasets: List[Dataset]):
        buckets = []
        if datasets:
            for dataset in datasets:
                buckets.append(f'arn:aws:s3:::{dataset.S3BucketName}/*')
                buckets.append(f'arn:aws:s3:::{dataset.S3BucketName}')

        return [
            iam.PolicyStatement(
                actions=['s3:*'],
                resources=buckets,
            )
        ]

