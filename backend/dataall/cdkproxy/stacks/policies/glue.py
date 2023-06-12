from .service_policy import ServicePolicy
from aws_cdk import aws_iam as iam


class GlueCatalog(ServicePolicy):
    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                sid="GlueLFReadData",
                effect=iam.Effect.ALLOW,
                actions=[
                    "lakeformation:GetDataAccess",
                    "glue:GetTable",
                    "glue:GetTables",
                    "glue:SearchTables",
                    "glue:GetDatabase",
                    "glue:GetDatabases",
                    "glue:GetPartitions",
                    "lakeformation:GetResourceLFTags",
                    "lakeformation:ListLFTags",
                    "lakeformation:GetLFTag",
                    "lakeformation:SearchTablesByLFTags",
                    "lakeformation:SearchDatabasesByLFTags"
                ],
                resources=["*"],
            ),
            iam.PolicyStatement(
                sid="GlueManageCatalog",
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
            )
        ]
        return statements


class Glue(ServicePolicy):
    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                sid="ListBucketProfilingGlue",
                actions=[
                    "s3:ListBucket",
                ],
                effect=iam.Effect.ALLOW,
                resources=[f'arn:aws:s3:::{self.environment.EnvironmentDefaultBucketName}'],
                conditions={"StringEquals": {
                    "s3:prefix": ["", "profiling/", "profiling/code/"],
                    "s3:delimiter": ["/"]}}
            ),
            iam.PolicyStatement(
                sid="ReadEnvironmentBucketProfilingGlue",
                actions=[
                    "s3:GetObject",
                    "s3:GetObjectAcl",
                    "s3:GetObjectVersion",
                ],
                resources=[
                    f'arn:aws:s3:::{self.environment.EnvironmentDefaultBucketName}/profiling/code/*'],
                effect=iam.Effect.ALLOW,
            ),
            iam.PolicyStatement(
                sid="GlueList",
                effect=iam.Effect.ALLOW,
                actions=[
                    'glue:Get*',
                    'glue:List*',
                    'glue:BatchGet*',
                ],
                resources=["*"],
            ),
            iam.PolicyStatement(
                sid="GlueCreateS3Bucket",
                effect=iam.Effect.ALLOW,
                actions=[
                    's3:CreateBucket',
                    's3:ListBucket',
                    's3:PutBucketPublicAccessBlock'
                ],
                resources=["arn:aws:s3:::aws-glue-*"],
            ),
            iam.PolicyStatement(
                sid="GlueReadWriteS3Bucket",
                actions=[
                    's3:GetObject',
                    's3:PutObject',
                    's3:DeleteObject'
                ],
                effect=iam.Effect.ALLOW,
                resources=[
                    'arn:aws:s3:::aws-glue-*/*',
                ],
            ),
            iam.PolicyStatement(
                sid="GlueCreate",
                effect=iam.Effect.ALLOW,
                actions=[
                    'glue:CreateDevEndpoint',
                    'glue:CreateCrawler',
                    'glue:CreateJob',
                    'glue:CreateTrigger',
                    'glue:TagResource',
                    'glue:UntagResource',
                ],
                resources=[
                    f'arn:aws:glue:{self.region}:{self.account}:crawler/{self.resource_prefix}*',
                    f'arn:aws:glue:{self.region}:{self.account}:job/{self.resource_prefix}*',
                    f'arn:aws:glue:{self.region}:{self.account}:devEndpoint/{self.resource_prefix}*',
                    f'arn:aws:glue:{self.region}:{self.account}:catalog',
                    f'arn:aws:glue:{self.region}:{self.account}:trigger/{self.resource_prefix}*',
                    f'arn:aws:glue:{self.region}:{self.account}:table/{self.resource_prefix}*/*',
                ],
                conditions={
                    'StringEquals': {f'aws:RequestTag/{self.tag_key}': [self.tag_value]}
                }
            ),
            iam.PolicyStatement(
                sid="GlueCrawler",
                effect=iam.Effect.ALLOW,
                actions=[
                    'glue:DeleteCrawler',
                    'glue:StartCrawler',
                    'glue:StopCrawler',
                    'glue:UpdateCrawler',
                    'glue:StartCrawlerSchedule',
                    'glue:UpdateCrawlerSchedule',
                    'glue:StopCrawlerSchedule',
                ],
                resources=[
                    f'arn:aws:glue:{self.region}:{self.account}:crawler/{self.resource_prefix}*'
                ],
                conditions={
                    'StringEquals': {
                        f'aws:resourceTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
            iam.PolicyStatement(
                sid="GlueJobs",
                effect=iam.Effect.ALLOW,
                actions=[
                    'glue:DeleteJob',
                    'glue:UpdateJob',
                    'glue:StartJobRun',
                    'glue:BatchStopJobRun'
                ],
                resources=[
                    f'arn:aws:glue:{self.region}:{self.account}:job/{self.resource_prefix}*'
                ],
                conditions={
                    'StringEquals': {
                        f'aws:resourceTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
            iam.PolicyStatement(
                sid="GlueDevEndpoints",
                effect=iam.Effect.ALLOW,
                actions=[
                    'glue:DeleteDevEndpoint',
                    'glue:UpdateDevEndpoint',
                ],
                resources=[
                    f'arn:aws:glue:{self.region}:{self.account}:devEndpoint/{self.resource_prefix}*',
                ],
                conditions={
                    'StringEquals': {
                        f'aws:resourceTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
            iam.PolicyStatement(
                sid="GlueTriggers",
                effect=iam.Effect.ALLOW,
                actions=[
                    'glue:DeleteTrigger',
                    'glue:StartTrigger',
                    'glue:StopTrigger',
                    'glue:UpdateTrigger',
                ],
                resources=[
                    f'arn:aws:glue:{self.region}:{self.account}:trigger/{self.resource_prefix}*',
                ],
                conditions={
                    'StringEquals': {
                        f'aws:resourceTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
            iam.PolicyStatement(
                sid="GlueClassifiers",
                effect=iam.Effect.ALLOW,
                actions=[
                    'glue:CreateClassifier',
                    'glue:UpdateClassifier',
                    'glue:DeleteClassifier'
                ],
                resources=['*'],
            ),
            iam.PolicyStatement(
                sid="SupportGluePermissions",
                effect=iam.Effect.ALLOW,
                actions=[
                    'glue:CreateScript',
                    'glue:CreateSecurityConfiguration',
                    'glue:DeleteSecurityConfiguration',
                ],
                resources=['*'],
            ),
            iam.PolicyStatement(
                sid="CreateLoggingGlue",
                actions=[
                    'logs:CreateLogGroup',
                    'logs:CreateLogStream',
                ],
                effect=iam.Effect.ALLOW,
                resources=[
                    f'arn:aws:logs:{self.region}:{self.account}:log-group:/aws-glue/*',
                ],
            ),
            iam.PolicyStatement(
                sid="LoggingGlue",
                actions=[
                    'logs:PutLogEvents',
                ],
                effect=iam.Effect.ALLOW,
                resources=[
                    f'arn:aws:logs:{self.region}:{self.account}:log-group:/aws-glue/*:log-stream:*',
                ],
            ),
        ]
        return statements
