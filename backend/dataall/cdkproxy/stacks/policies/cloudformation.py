from .service_policy import ServicePolicy
from aws_cdk import aws_iam as iam


class Cloudformation(ServicePolicy):
    """
    Class including all permissions needed to work with AWS CloudFormation.
    It allows data.all users to:
    - Create/Delete CloudFormation team stacks
    - Create an S3 Bucket for codepipeline prefixed by "cf-templates-"
    - Read/Write to and from S3 Buckets prefixed by "cf-templates-"
    """
    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                sid="GenericCloudFormation",
                actions=[
                    'cloudformation:EstimateTemplateCost',
                    'cloudformation:ListStacks',
                    'cloudformation:ValidateTemplate',
                    'cloudformation:GetTemplateSummary',
                    'cloudformation:ListExports',
                    'cloudformation:ListImports',
                    'cloudformation:DescribeAccountLimits',
                    'cloudformation:DescribeStackDriftDetectionStatus',
                    'cloudformation:Cancel*',
                    'cloudformation:Continue*',
                    'cloudformation:CreateChangeSet',
                    'cloudformation:ExecuteChangeSet',
                    'cloudformation:CreateStackSet',
                    'cloudformation:Get*',
                    'cloudformation:Describe*',
                    'cloudformation:List*',
                    'cloudformation:CreateUploadBucket',
                ],
                resources=['*'],
            ),
            iam.PolicyStatement(
                sid="CloudFormationCreateS3Bucket",
                effect=iam.Effect.ALLOW,
                actions=[
                    's3:ListBucket',
                    's3:PutBucketPublicAccessBlock'
                ],
                resources=["arn:aws:s3:::cf-templates-*"],
            ),
            iam.PolicyStatement(
                sid="CloudFormationReadWriteS3Bucket",
                actions=[
                    's3:GetObject',
                    's3:PutObject',
                    's3:DeleteObject'
                ],
                effect=iam.Effect.ALLOW,
                resources=[
                    'arn:aws:s3:::cf-templates-*/*',
                ],
            ),
            iam.PolicyStatement(
                sid="CreateTeamCloudFormation",
                actions=[
                    'cloudformation:CreateStack',
                ],
                resources=[
                    f'arn:aws:cloudformation:{self.region}:{self.account}:*/{self.resource_prefix}*'
                ],
                conditions={
                    'StringEquals': {f'aws:RequestTag/{self.tag_key}': [self.tag_value]}
                },
            ),
            iam.PolicyStatement(
                sid="DeleteTeamCloudFormation",
                actions=[
                    'cloudformation:DeleteStack',
                ],
                resources=[
                    f'arn:aws:cloudformation:{self.region}:{self.account}:*/{self.resource_prefix}*'
                ],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
        ]
        return statements
