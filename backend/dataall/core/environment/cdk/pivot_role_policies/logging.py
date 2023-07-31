from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from aws_cdk import aws_iam as iam


class Logging(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with AWS CloudFormation.
    It allows pivot role to:
    - ....
    """
    def get_statements(self):
        statements = [
            # CloudWatch Metrics
            iam.PolicyStatement(
                sid='CWMetrics',
                effect=iam.Effect.ALLOW,
                actions=[
                    'cloudwatch:PutMetricData',
                    'cloudwatch:GetMetricData',
                    'cloudwatch:GetMetricStatistics'
                ],
                resources=['*'],
            ),
            # Logs
            iam.PolicyStatement(
                sid='Logs',
                effect=iam.Effect.ALLOW,
                actions=[
                    'logs:CreateLogGroup',
                    'logs:CreateLogStream',
                ],
                resources=[
                    f'arn:aws:logs:*:{self.account}:log-group:/aws/lambda/*',
                    f'arn:aws:logs:*:{self.account}:log-group:/{self.env_resource_prefix}*',
                ],
            ),
            # Logging
            iam.PolicyStatement(
                sid='Logging', effect=iam.Effect.ALLOW, actions=['logs:PutLogEvents'], resources=['*']
            ),
        ]
        return statements
