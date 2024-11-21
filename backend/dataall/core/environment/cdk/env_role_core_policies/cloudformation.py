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

    def get_statements(self, group_permissions, **kwargs):
        statements = [
            iam.PolicyStatement(
                # sid="GenericCloudFormation",
                actions=[
                    'cloudformation:EstimateTemplateCost',
                    'cloudformation:ListStacks',
                    'cloudformation:ValidateTemplate',
                    'cloudformation:GetTemplateSummary',
                    'cloudformation:ListExports',
                    'cloudformation:ListImports',
                    'cloudformation:DescribeAccountLimits',
                    'cloudformation:DescribeStackDriftDetectionStatus',
                    'cloudformation:CreateStackSet',
                    'cloudformation:Get*',
                    'cloudformation:Describe*',
                    'cloudformation:List*',
                    'cloudformation:CreateUploadBucket',
                ],
                resources=['*'],
            ),
            iam.PolicyStatement(
                actions=[
                    'cloudformation:Cancel*',
                    'cloudformation:Continue*',
                    'cloudformation:CreateChangeSet',
                    'cloudformation:ExecuteChangeSet',
                ],
                resources=[f'arn:aws:cloudformation:*:{self.account}:*/{self.resource_prefix}*'],
            ),
            iam.PolicyStatement(
                # sid="DeleteTeamCloudFormation",
                actions=[
                    'cloudformation:DeleteStack',
                ],
                resources=[f'arn:aws:cloudformation:{self.region}:{self.account}:*/{self.resource_prefix}*'],
                conditions={'StringEquals': {f'aws:ResourceTag/{self.tag_key}': [self.tag_value]}},
            ),
        ]
        return statements
