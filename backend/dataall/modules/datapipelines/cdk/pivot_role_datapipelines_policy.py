from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from aws_cdk import aws_iam as iam


class PipelinesPivotRole(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with AWS CodeCommit and STS assume for DDK pipelines
    It allows pivot role to:
    - ....
    """
    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                sid='CodeCommitPipelines',
                effect=iam.Effect.ALLOW,
                actions=[
                    'codecommit:GetFile',
                    'codecommit:ListBranches',
                    'codecommit:GetFolder',
                    'codecommit:GetCommit',
                    'codecommit:GitPull',
                    'codecommit:GetRepository',
                    'codecommit:TagResource',
                    'codecommit:UntagResource',
                    'codecommit:CreateBranch',
                    'codecommit:CreateCommit',
                    'codecommit:CreateRepository',
                    'codecommit:DeleteRepository',
                    'codecommit:GitPush',
                    'codecommit:PutFile',
                    'codecommit:GetBranch',
                ],
                resources=[f'arn:aws:codecommit:*:{self.account}:{self.env_resource_prefix}*'],
            ),
            iam.PolicyStatement(
                sid='STSPipelines',
                effect=iam.Effect.ALLOW,
                actions=['sts:AssumeRole'],
                resources=[
                    f'arn:aws:iam::{self.account}:role/ddk-*',
                ],
            ),
            iam.PolicyStatement(
                sid='CloudFormationDataPipelines',
                effect=iam.Effect.ALLOW,
                actions=[
                    "cloudformation:DeleteStack",
                    "cloudformation:DescribeStacks",
                    "cloudformation:DescribeStackEvents",
                    "cloudformation:DescribeStackResources"
                ],
                resources=[
                    f'arn:aws:cloudformation:*:{self.account}:stack/*/*',
                ],
            ),
            iam.PolicyStatement(
                sid='ParameterStoreDDK',
                effect=iam.Effect.ALLOW,
                actions=['ssm:GetParameter'],
                resources=[
                    f'arn:aws:ssm:*:{self.account}:parameter/ddk/*',
                ],
            ),
        ]
        return statements
