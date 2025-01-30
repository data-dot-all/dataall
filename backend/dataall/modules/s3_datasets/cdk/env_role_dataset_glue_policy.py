from dataall.core.environment.cdk.env_role_core_policies.service_policy import ServicePolicy
from aws_cdk import aws_iam as iam

from dataall.modules.s3_datasets.services.dataset_permissions import CREATE_DATASET


class DatasetGlueCatalogServicePolicy(ServicePolicy):
    """
    Class including all permissions needed to work with AWS Glue Catalog.
    """

    def get_statements(self, group_permissions, **kwargs):
        statements = [
            iam.PolicyStatement(
                # sid="GlueLFReadData",
                effect=iam.Effect.ALLOW,
                actions=[
                    'lakeformation:GetDataAccess',
                    'glue:GetTable',
                    'glue:GetTables',
                    'glue:SearchTables',
                    'glue:GetDatabase',
                    'glue:GetDatabases',
                    'glue:GetPartitions',
                    'lakeformation:GetResourceLFTags',
                    'lakeformation:ListLFTags',
                    'lakeformation:GetLFTag',
                    'lakeformation:SearchTablesByLFTags',
                    'lakeformation:SearchDatabasesByLFTags',
                ],
                resources=['*'],
            ),
            iam.PolicyStatement(
                # sid="GlueManageCatalog",
                actions=[
                    'glue:CreateConnection',
                    'glue:CreateDatabase',
                    'glue:CreatePartition',
                    'glue:CreateTable',
                    'glue:CreateUserDefinedFunction',
                    'glue:DeleteConnection',
                    'glue:DeleteDatabase',
                    'glue:DeleteTable',
                    'glue:DeleteTableVersion',
                    'glue:DeleteUserDefinedFunction',
                    'glue:UpdateConnection',
                    'glue:UpdateDatabase',
                    'glue:UpdatePartition',
                    'glue:UpdateTable',
                    'glue:UpdateUserDefinedFunction',
                    'glue:BatchCreatePartition',
                    'glue:BatchDeleteConnection',
                    'glue:BatchDeletePartition',
                    'glue:BatchDeleteTable',
                    'glue:BatchDeleteTableVersion',
                    'glue:BatchGetPartition',
                ],
                resources=[
                    f'arn:aws:glue:{self.region}:{self.account}:userDefinedFunction/{self.resource_prefix}*/*',
                    f'arn:aws:glue:{self.region}:{self.account}:database/{self.resource_prefix}*',
                    f'arn:aws:glue:{self.region}:{self.account}:catalog',
                    f'arn:aws:glue:{self.region}:{self.account}:table/{self.resource_prefix}*/*',
                    f'arn:aws:glue:{self.region}:{self.account}:connection/{self.resource_prefix}*',
                ],
            ),
        ]
        return statements


class DatasetGlueEtlServicePolicy(ServicePolicy):
    """
    Class including all permissions needed to work with AWS Glue ETL.
    """

    def get_statements(self, group_permissions, **kwargs):
        statements = [
            iam.PolicyStatement(
                # sid="ListBucketProfilingGlue",
                actions=[
                    's3:ListBucket',
                ],
                effect=iam.Effect.ALLOW,
                resources=[f'arn:aws:s3:::{self.environment.EnvironmentDefaultBucketName}'],
                conditions={
                    'StringEquals': {'s3:prefix': ['', 'profiling/', 'profiling/code/'], 's3:delimiter': ['/']}
                },
            ),
            iam.PolicyStatement(
                # sid="ReadEnvironmentBucketProfilingGlue",
                actions=[
                    's3:GetObject',
                    's3:GetObjectAcl',
                    's3:GetObjectVersion',
                ],
                resources=[f'arn:aws:s3:::{self.environment.EnvironmentDefaultBucketName}/profiling/code/*'],
                effect=iam.Effect.ALLOW,
            ),
            iam.PolicyStatement(
                # sid="GlueList",
                effect=iam.Effect.ALLOW,
                actions=[
                    'glue:Get*',
                    'glue:ListDevEndpoints',
                    'glue:ListBlueprints',
                    'glue:ListRegistries',
                    'glue:ListTriggers',
                    'glue:ListUsageProfiles',
                    'glue:ListCrawlers',
                    'glue:ListCrawls',
                    'glue:ListJobs',
                    'glue:ListCustomEntityTypes',
                    'glue:ListSessions',
                    'glue:ListWorkflows',
                    'glue:BatchGet*',
                ],
                resources=['*'],
            ),
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    'glue:ListDataQualityRuleRecommendationRuns',
                    'glue:ListSchemaVersions',
                    'glue:QuerySchemaVersionMetadata',
                    'glue:ListMLTransforms',
                    'glue:ListStatements',
                    'glue:ListSchemas',
                    'glue:ListDataQualityRulesetEvaluationRuns',
                    'glue:ListTableOptimizerRuns',
                    'glue:GetMLTaskRuns',
                    'glue:ListDataQualityRulesets',
                    'glue:ListDataQualityResults',
                    'glue:GetMLTransforms',
                ],
                resources=[
                    f'arn:aws:glue:*:{self.account}:schema/*',
                    f'arn:aws:glue:*:{self.account}:registry/*',
                    f'arn:aws:glue:*:{self.account}:dataQualityRuleset/*',
                    f'arn:aws:glue:*:{self.account}:table/*/*',
                    f'arn:aws:glue:*:{self.account}:database/*',
                    f'arn:aws:glue:*:{self.account}:mlTransform/*',
                    f'arn:aws:glue:*:{self.account}:catalog',
                    f'arn:aws:glue:*:{self.account}:session/*',
                ],
            ),
            iam.PolicyStatement(
                # sid="GlueCreateS3Bucket",
                effect=iam.Effect.ALLOW,
                actions=['s3:CreateBucket', 's3:ListBucket', 's3:PutBucketPublicAccessBlock'],
                resources=[f'arn:aws:s3:::aws-glue-assets-{self.account}-{self.region}'],
            ),
            iam.PolicyStatement(
                # sid="GlueReadWriteS3Bucket",
                actions=['s3:GetObject', 's3:PutObject', 's3:DeleteObject'],
                effect=iam.Effect.ALLOW,
                resources=[
                    f'arn:aws:s3:::aws-glue-assets-{self.account}-{self.region}/{self.resource_prefix}/{self.team.groupUri}/',
                    f'arn:aws:s3:::aws-glue-assets-{self.account}-{self.region}/{self.resource_prefix}/{self.team.groupUri}/*',
                ],
            ),
            iam.PolicyStatement(
                # sid="GlueCreate",
                effect=iam.Effect.ALLOW,
                actions=[
                    'glue:CreateDevEndpoint',
                    'glue:CreateCrawler',
                    'glue:CreateJob',
                    'glue:CreateTrigger',
                    'glue:TagResource',
                ],
                resources=[
                    f'arn:aws:glue:{self.region}:{self.account}:crawler/{self.resource_prefix}*',
                    f'arn:aws:glue:{self.region}:{self.account}:job/{self.resource_prefix}*',
                    f'arn:aws:glue:{self.region}:{self.account}:devEndpoint/{self.resource_prefix}*',
                    f'arn:aws:glue:{self.region}:{self.account}:catalog',
                    f'arn:aws:glue:{self.region}:{self.account}:trigger/{self.resource_prefix}*',
                    f'arn:aws:glue:{self.region}:{self.account}:table/{self.resource_prefix}*/*',
                ],
                conditions={'StringEquals': {f'aws:RequestTag/{self.tag_key}': [self.tag_value]}},
            ),
            iam.PolicyStatement(
                # sid="GlueManageGlueResources",
                effect=iam.Effect.ALLOW,
                not_actions=[
                    'glue:CreateDevEndpoint',
                    'glue:CreateTrigger',
                    'glue:CreateJob',
                    'glue:CreateCrawler',
                ],
                resources=[
                    f'arn:aws:glue:{self.region}:{self.account}:devEndpoint/{self.resource_prefix}*',
                    f'arn:aws:glue:{self.region}:{self.account}:trigger/{self.resource_prefix}*',
                    f'arn:aws:glue:{self.region}:{self.account}:job/{self.resource_prefix}*',
                    f'arn:aws:glue:{self.region}:{self.account}:crawler/{self.resource_prefix}*',
                ],
                conditions={'StringEquals': {f'aws:resourceTag/{self.tag_key}': [self.tag_value]}},
            ),
            iam.PolicyStatement(
                # sid="SupportGluePermissions",
                effect=iam.Effect.ALLOW,
                actions=[
                    'glue:*Classifier',
                    'glue:CreateScript',
                ],
                resources=['*'],
            ),
            iam.PolicyStatement(
                # sid="LoggingGlue",
                actions=[
                    'logs:CreateLogGroup',
                    'logs:CreateLogStream',
                    'logs:PutLogEvents',
                ],
                effect=iam.Effect.ALLOW,
                resources=[
                    f'arn:aws:logs:{self.region}:{self.account}:log-group:/aws-glue/*',
                    f'arn:aws:logs:{self.region}:{self.account}:log-group:/aws-glue/*:log-stream:*',
                ],
            ),
        ]
        return statements
