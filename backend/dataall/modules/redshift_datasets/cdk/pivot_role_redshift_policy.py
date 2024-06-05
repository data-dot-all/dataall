from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from aws_cdk import aws_iam as iam


class RedshiftDatasetsPivotRole(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with Amazon Redshift.
    It allows pivot role to:
    - redshift-data:ExecuteStatement on resource: arn:aws:redshift-serverless:eu-west-1:796821004569:workgroup/e49614d2-01b9-431d-ba41-e5b36db93dd0
    """

    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                sid='RedshiftDataAPIActions',
                effect=iam.Effect.ALLOW,
                actions=[
                    'redshift-data:ExecuteStatement',
                ],
                resources=[
                    f'arn:aws:redshift-serverless:{self.region}:{self.account}:workgroup/*',
                    f'arn:aws:redshift:{self.region}:{self.account}:cluster/*',  # TODO: SCOPE DOWN PERMISSIONS
                ],
            )
        ]
        return statements
