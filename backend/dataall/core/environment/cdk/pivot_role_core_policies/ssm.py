from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from aws_cdk import aws_iam as iam


class SSMPivotRole(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with AWS SSM.
    It allows pivot role to:
    - ....
    """

    def get_statements(self):
        statements = [
            # SSM Parameter Store
            iam.PolicyStatement(
                sid='ParameterStore',
                effect=iam.Effect.ALLOW,
                actions=['ssm:GetParameter'],
                resources=[
                    f'arn:aws:ssm:*:{self.account}:parameter/{self.env_resource_prefix}/*',
                    f'arn:aws:ssm:*:{self.account}:parameter/dataall/*',
                ],
            ),
        ]
        return statements
