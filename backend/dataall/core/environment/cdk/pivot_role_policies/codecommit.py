from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from aws_cdk import aws_iam as iam


class CodeCommit(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with AWS CloudFormation.
    It allows pivot role to:
    - ....
    """
    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                sid='CodeCommit',
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
        ]
        return statements
