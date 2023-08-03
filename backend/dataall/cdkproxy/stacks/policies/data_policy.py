import logging
from typing import List

from aws_cdk import aws_iam as iam
from ....aws.handlers.kms import KMS

from ....db import models

logger = logging.getLogger()


class DataPolicy:
    """
    Class including all permissions needed to work with AWS Lambda.
    It allows data.all users to:
    -
    """
    def __init__(
        self,
        stack,
        id,
        name,
        account,
        region,
        tag_key,
        tag_value,
        resource_prefix,
        environment: models.Environment,
        team: models.EnvironmentGroup,
        datasets: [models.Dataset],
    ):
        self.stack = stack
        self.id = id
        self.name = name
        self.account = account
        self.region = region
        self.tag_key = tag_key
        self.tag_value = tag_value
        self.resource_prefix = resource_prefix
        self.environment = environment
        self.team = team
        self.datasets = datasets

    def generate_data_access_policy(self) -> iam.Policy:
        """
        Creates aws_iam.Policy based on team datasets
        """
        statements: List[iam.PolicyStatement] = self.get_statements()

        policy: iam.Policy = iam.Policy(
            self.stack,
            self.id,
            policy_name=self.name,
            statements=statements,
        )
        logger.debug(f'Final generated policy {policy.document.to_json()}')

        return policy

    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                sid="ListAll",
                actions=[
                    "s3:ListAllMyBuckets",
                    "s3:ListAccessPoints",
                    "s3:GetBucketLocation",
                    'kms:ListAliases',
                    'kms:ListKeys',
                ],
                resources=["*"],
                effect=iam.Effect.ALLOW
            )
        ]

        self.set_allowed_s3_buckets_statements(statements)
        self.set_allowed_kms_keys_statements(statements)

        return statements

    def set_allowed_s3_buckets_statements(self, statements):
        allowed_buckets = []
        allowed_access_points = []
        if self.datasets:
            dataset: models.Dataset
            for dataset in self.datasets:
                allowed_buckets.append(f'arn:aws:s3:::{dataset.S3BucketName}')
                allowed_access_points.append(f'arn:aws:s3:{dataset.region}:{dataset.AwsAccountId}:accesspoint/{dataset.datasetUri}*')
            allowed_buckets_content = [f"{bucket}/*" for bucket in allowed_buckets]
            statements.extend(
                [
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
                    )
                ]
            )

    def set_allowed_kms_keys_statements(self, statements):
        allowed_buckets_kms_keys = []
        if self.datasets:
            dataset: models.Dataset
            for dataset in self.datasets:
                if dataset.imported and dataset.importedKmsKey:
                    key_id = KMS.get_key_id(
                        account_id=dataset.AwsAccountId,
                        region=dataset.region,
                        key_alias=f"alias/{dataset.KmsAlias}"
                    )
                    if key_id:
                        allowed_buckets_kms_keys.append(f"arn:aws:kms:{dataset.region}:{dataset.AwsAccountId}:key/{key_id}")
            if len(allowed_buckets_kms_keys):
                statements.extend(
                    [
                        iam.PolicyStatement(
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
                    ]
                )
