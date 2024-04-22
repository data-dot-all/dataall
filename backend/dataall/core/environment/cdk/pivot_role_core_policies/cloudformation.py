from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from aws_cdk import aws_iam as iam


class CloudformationPivotRole(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with AWS CloudFormation.
    It allows pivot role to:
    - ....
    """

    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                sid='CloudFormation',
                effect=iam.Effect.ALLOW,
                actions=[
                    'cloudformation:DeleteStack',
                    'cloudformation:DescribeStacks',
                    'cloudformation:DescribeStackEvents',
                    'cloudformation:DescribeStackResources',
                    'cloudformation:ContinueUpdateRollback',
                ],
                resources=[
                    f'arn:aws:cloudformation:*:{self.account}:stack/{self.env_resource_prefix}*/*',
                    f'arn:aws:cloudformation:*:{self.account}:stack/CDKToolkit/*',
                ],
            ),
        ]
        return statements
