from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from aws_cdk import aws_iam as iam


class EC2(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with AWS CloudFormation.
    It allows pivot role to:
    - ....
    """
    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                sid='EC2SG',
                effect=iam.Effect.ALLOW,
                actions=[
                    'ec2:DescribeSubnets',
                    'ec2:DescribeSecurityGroups',
                    'ec2:DescribeVpcs',
                    'ec2:DescribeInstances',
                    'ec2:DescribeNetworkInterfaces',
                ],
                resources=['*'],
            ),
        ]
        return statements
