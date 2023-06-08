import logging
from typing import List

from aws_cdk import aws_iam as iam

from ....db import models

logger = logging.getLogger()


class DataPolicy:
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
                ],
                resources=["*"],
                effect=iam.Effect.ALLOW
            )
        ]

        self.set_allowed_s3_buckets_statements(statements)

        self.set_athena_statements(statements)

        return statements

    def set_allowed_s3_buckets_statements(self, statements):
        allowed_buckets = []
        allowed_buckets_content = []
        allowed_buckets_kms_aliases = []
        allowed_access_points = []
        if self.datasets:
            dataset: models.Dataset
            for dataset in self.datasets:
                allowed_buckets.append(f'arn:aws:s3:::{dataset.S3BucketName}')
                allowed_buckets_content.append(f'arn:aws:s3:::{dataset.S3BucketName}/*')
                allowed_buckets_kms_aliases.append(dataset.KmsAlias)
                allowed_access_points.append(f'arn:aws:s3:{dataset.region}:{dataset.AwsAccountId}:accesspoint/{dataset.datasetUri}*')
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
                    sid="KMSAccess",
                    actions=[
                        "kms:Decrypt",
                        "kms:Encrypt",
                        "kms:GenerateDataKey"
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=["*"],
                    condition=("StringEquals", {"kms:RequestAlias": allowed_buckets_kms_aliases})
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

    def set_athena_statements(self, statements):
        statements.extend(
            [
                iam.PolicyStatement(
                    sid="AthenaReadAll",
                    actions=[
                        "athena:ListEngineVersions",
                        "athena:ListWorkGroups",
                        "athena:ListDataCatalogs",
                        "athena:ListDatabases",
                        "athena:GetDatabase",
                        "athena:ListTableMetadata",
                        "athena:GetTableMetadata"
                    ],
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    sid="AthenaReadAll",
                    actions=[
                        "athena:GetWorkGroup",
                        "athena:BatchGetQueryExecution",
                        "athena:GetQueryExecution",
                        "athena:ListQueryExecutions",
                        "athena:StartQueryExecution",
                        "athena:StopQueryExecution",
                        "athena:GetQueryResults",
                        "athena:GetQueryResultsStream",
                        "athena:CreateNamedQuery",
                        "athena:GetNamedQuery",
                        "athena:BatchGetNamedQuery",
                        "athena:ListNamedQueries",
                        "athena:DeleteNamedQuery",
                        "athena:CreatePreparedStatement",
                        "athena:GetPreparedStatement",
                        "athena:ListPreparedStatements",
                        "athena:UpdatePreparedStatement",
                        "athena:DeletePreparedStatement"
                    ],
                    resources=[f'arn:aws:athena:{self.region}:{self.account}:workgroup/{self.team.environmentAthenaWorkGroup}'],
                ),
                iam.PolicyStatement(
                    sid="ReadEnvironmentBucketAthenaQueries",
                    actions=[
                        "s3:GetObject",
                        "s3:GetObjectAcl",
                        "s3:GetObjectVersion"
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=[f'arn:aws:s3:::{self.environment.EnvironmentDefaultBucketName}/athenaqueries*'],
                ),
                iam.PolicyStatement(
                    sid="ReadWriteEnvironmentBucketAthenaQueries",
                    actions=[
                        "s3:PutObject",
                        "s3:PutObjectAcl",
                        "s3:GetObject",
                        "s3:GetObjectAcl",
                        "s3:GetObjectVersion",
                        "s3:DeleteObject"
                    ],
                    resources=[
                        f'arn:aws:s3:::{self.environment.EnvironmentDefaultBucketName}/athenaqueries/{self.team.groupUri}/*'],
                    effect=iam.Effect.ALLOW,
                ),
            ]
        )
