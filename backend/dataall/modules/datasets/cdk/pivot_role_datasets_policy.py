import os
from dataall.base import db
from dataall.base.utils.iam_policy_utils import split_policy_with_resources_in_statements
from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from dataall.modules.datasets_base.db.dataset_repositories import DatasetRepository
from dataall.modules.datasets_base.db.dataset_models import Dataset
from aws_cdk import aws_iam as iam


class DatasetsPivotRole(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with Datasets based in S3 and Glue databases
    It allows pivot role to:
    - ....
    """
    def get_statements(self):
        statements = [
            # For dataset preview
            iam.PolicyStatement(
                sid='AthenaWorkgroupsDataset',
                effect=iam.Effect.ALLOW,
                actions=[
                    "athena:GetQueryExecution",
                    "athena:GetQueryResults",
                    "athena:GetWorkGroup",
                    "athena:StartQueryExecution"
                ],
                resources=[f'arn:aws:athena:*:{self.account}:workgroup/{self.env_resource_prefix}*'],
            ),
            # For Glue database management
            iam.PolicyStatement(
                sid='GlueCatalog',
                effect=iam.Effect.ALLOW,
                actions=[
                    'glue:BatchCreatePartition',
                    'glue:BatchDeletePartition',
                    'glue:BatchDeleteTable',
                    'glue:CreateDatabase',
                    'glue:CreatePartition',
                    'glue:CreateTable',
                    'glue:DeleteDatabase',
                    'glue:DeletePartition',
                    'glue:DeleteTable',
                    'glue:BatchGet*',
                    'glue:Get*',
                    'glue:List*',
                    'glue:SearchTables',
                    'glue:UpdateDatabase',
                    'glue:UpdatePartition',
                    'glue:UpdateTable',
                    'glue:TagResource',
                    'glue:DeleteResourcePolicy',
                    'glue:PutResourcePolicy',
                ],
                resources=['*'],
            ),
            # Manage LF permissions for glue databases
            iam.PolicyStatement(
                sid='LakeFormation',
                effect=iam.Effect.ALLOW,
                actions=[
                    'lakeformation:UpdateResource',
                    'lakeformation:DescribeResource',
                    'lakeformation:AddLFTagsToResource',
                    'lakeformation:RemoveLFTagsFromResource',
                    'lakeformation:GetResourceLFTags',
                    'lakeformation:ListLFTags',
                    'lakeformation:CreateLFTag',
                    'lakeformation:GetLFTag',
                    'lakeformation:UpdateLFTag',
                    'lakeformation:DeleteLFTag',
                    'lakeformation:SearchTablesByLFTags',
                    'lakeformation:SearchDatabasesByLFTags',
                    'lakeformation:ListResources',
                    'lakeformation:ListPermissions',
                    'lakeformation:GrantPermissions',
                    'lakeformation:BatchGrantPermissions',
                    'lakeformation:RevokePermissions',
                    'lakeformation:BatchRevokePermissions',
                    'lakeformation:PutDataLakeSettings',
                    'lakeformation:GetDataLakeSettings',
                    'lakeformation:GetDataAccess',
                    'lakeformation:GetWorkUnits',
                    'lakeformation:StartQueryPlanning',
                    'lakeformation:GetWorkUnitResults',
                    'lakeformation:GetQueryState',
                    'lakeformation:GetQueryStatistics',
                    'lakeformation:GetTableObjects',
                    'lakeformation:UpdateTableObjects',
                    'lakeformation:DeleteObjectsOnCancel',
                ],
                resources=['*'],
            ),
            # Glue ETL - needed to start crawler and profiling jobs
            iam.PolicyStatement(
                sid='GlueETL',
                effect=iam.Effect.ALLOW,
                actions=[
                    'glue:StartCrawler',
                    'glue:StartJobRun',
                    'glue:StartTrigger',
                    'glue:UpdateTrigger',
                    'glue:UpdateJob',
                    'glue:UpdateCrawler',
                ],
                resources=[
                    f'arn:aws:glue:*:{self.account}:crawler/{self.env_resource_prefix}*',
                    f'arn:aws:glue:*:{self.account}:job/{self.env_resource_prefix}*',
                    f'arn:aws:glue:*:{self.account}:trigger/{self.env_resource_prefix}*',
                ],
            ),
            iam.PolicyStatement(
                sid="PassRoleGlue",
                actions=[
                    'iam:PassRole',
                ],
                resources=[
                    f'arn:aws:iam::{self.account}:role/{self.env_resource_prefix}*',
                ],
                conditions={
                    "StringEquals": {
                        "iam:PassedToService": [
                            "glue.amazonaws.com",
                        ]
                    }
                }
            )
        ]
        allowed_buckets = []
        engine = db.get_engine(envname=os.environ.get('envname', 'local'))
        with engine.scoped_session() as session:
            datasets = DatasetRepository.query_environment_imported_datasets(
                session, uri=self.environmentUri, filter=None
            )
            if datasets:
                dataset: Dataset
                for dataset in datasets:
                    allowed_buckets.append(f'arn:aws:s3:::{dataset.S3BucketName}')
                for i in range(10):
                    allowed_buckets.append(f'arn:aws:s3:::fakedataset-{i}')

        if allowed_buckets:
            # Imported Dataset S3 Buckets, created bucket permissions are added in core S3 permissions

            base_statement = iam.PolicyStatement(
                sid='ImportedDatasetBuckets',
                effect=iam.Effect.ALLOW,
                actions=[
                    's3:List*',
                    's3:GetBucket*',
                    's3:GetLifecycleConfiguration',
                    's3:GetObject',
                    's3:PutBucketPolicy',
                    's3:PutBucketTagging',
                    's3:PutObjectAcl',
                    's3:PutBucketOwnershipControls',
                ],
                resources="RESOURCES",
            )
            dataset_statement = split_policy_with_resources_in_statements(
                statement_without_resources=base_statement,
                resources=allowed_buckets
            )
            statements.extend(dataset_statement)
        return statements
