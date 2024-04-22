from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from aws_cdk import aws_iam as iam


class LoggingPivotRole(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with AWS CloudWatch.
    It allows pivot role to:
    - ....
    """

    def get_statements(self):
        statements = [
            # CloudWatch Metrics
            iam.PolicyStatement(
                sid='CWMetrics',
                effect=iam.Effect.ALLOW,
                actions=['cloudwatch:PutMetricData', 'cloudwatch:GetMetricData', 'cloudwatch:GetMetricStatistics'],
                resources=['*'],
            ),
            # Logs
            iam.PolicyStatement(
                sid='Logs',
                effect=iam.Effect.ALLOW,
                actions=[
                    'logs:CreateLogGroup',
                    'logs:CreateLogStream',
                    'logs:PutLogEvents',
                ],
                resources=[
                    f'arn:aws:logs:*:{self.account}:log-group:/aws/lambda/{self.env_resource_prefix}*',
                    f'arn:aws:logs:*:{self.account}:log-group:/{self.env_resource_prefix}*',
                ],
            ),
        ]
        return statements
