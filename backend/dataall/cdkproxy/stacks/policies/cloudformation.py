from .service_policy import ServicePolicy
from aws_cdk import aws_iam as iam


class Cloudformation(ServicePolicy):
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
                ],
                resources=['*'],
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
                sid="ManagedTeamCloudFormation",
                actions=[
                    'cloudformation:UpdateStack',
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
