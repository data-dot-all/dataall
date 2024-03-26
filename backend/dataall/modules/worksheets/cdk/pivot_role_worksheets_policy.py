from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from aws_cdk import aws_iam as iam


class WorksheetsPivotRole(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with Athena
    It allows pivot role to:
    - ....
    """

    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                sid='AthenaWorkgroups',
                effect=iam.Effect.ALLOW,
                actions=[
                    'athena:GetQueryExecution',
                    'athena:GetQueryResults',
                    'athena:GetWorkGroup',
                    'athena:StartQueryExecution',
                ],
                resources=[f'arn:aws:athena:*:{self.account}:workgroup/{self.env_resource_prefix}*'],
            )
        ]
        return statements
