from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from aws_cdk import aws_iam as iam


class STSPivotRole(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with AWS STS.
    It allows pivot role to:
    - ....
    """

    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                sid='STS',
                effect=iam.Effect.ALLOW,
                actions=['sts:AssumeRole'],
                resources=[f'arn:aws:iam::{self.account}:role/{self.env_resource_prefix}*'],
            ),
        ]
        return statements
