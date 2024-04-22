from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from aws_cdk import aws_iam as iam


class SQSPivotRole(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with AWS SQS.
    It allows pivot role to:
    - ....
    """

    def get_statements(self):
        statements = [
            # SQS - support SQS queues
            iam.PolicyStatement(sid='SQSList', effect=iam.Effect.ALLOW, actions=['sqs:ListQueues'], resources=['*']),
            iam.PolicyStatement(
                sid='SQS',
                effect=iam.Effect.ALLOW,
                actions=['sqs:ReceiveMessage', 'sqs:SendMessage'],
                resources=[f'arn:aws:sqs:*:{self.account}:{self.env_resource_prefix}*'],
            ),
        ]
        return statements
