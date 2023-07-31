from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from aws_cdk import aws_iam as iam


class IAM(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with AWS CloudFormation.
    It allows pivot role to:
    - ....
    """
    def get_statements(self):
        statements = [
            # IAM - needed for consumption roles and for S3 sharing
            iam.PolicyStatement(
                sid='IAMListGet',
                effect=iam.Effect.ALLOW,
                actions=[
                    'iam:ListRoles',
                    'iam:Get*'
                ], resources=['*']
            ),
            iam.PolicyStatement(
                sid='IAMRolePolicy',
                effect=iam.Effect.ALLOW,
                actions=[
                    'iam:PutRolePolicy',
                    'iam:DeleteRolePolicy'
                ],
                resources=['*'],
            ),
            iam.PolicyStatement(
                sid="PassRole",
                actions=[
                    'iam:PassRole',
                ],
                resources=[
                    f'arn:aws:iam::{self.account}:role/{self.role_name}',
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
            ),
        ]
        return statements
