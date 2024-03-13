from .service_policy import ServicePolicy
from aws_cdk import aws_iam


class SQS(ServicePolicy):
    """
    Class including all permissions needed to work with AWS SQS queues.
    """

    def get_statements(self, group_permissions, **kwargs):
        statements = [
            aws_iam.PolicyStatement(
                # sid='SQSRead',
                effect=aws_iam.Effect.ALLOW,
                actions=[
                    'sqs:ListQueues',
                ],
                resources=['*'],
            ),
            aws_iam.PolicyStatement(
                # sid='SQSCreate',
                effect=aws_iam.Effect.ALLOW,
                actions=[
                    'sqs:CreateQueue',
                    'sqs:TagQueue',
                ],
                resources=[f'arn:aws:sqs:*:{self.account}:{self.resource_prefix}*'],
                conditions={'StringEquals': {f'aws:RequestTag/{self.tag_key}': [self.tag_value]}},
            ),
            aws_iam.PolicyStatement(
                # sid='SQSManageTeamQueue',
                effect=aws_iam.Effect.ALLOW,
                actions=[
                    'sqs:GetQueueUrl',
                    'sqs:DeleteQueue',
                    'sqs:GetQueueAttributes',
                    'sqs:SetQueueAttributes',
                    'sqs:ListQueueTags',
                    'sqs:ListDeadLetterSourceQueues',
                    'sqs:SendMessage',
                    'sqs:ReceiveMessage',
                    'sqs:DeleteMessage',
                    'sqs:ChangeMessageVisibility',
                ],
                resources=[f'arn:aws:sqs:*:{self.account}:{self.resource_prefix}*'],
                conditions={'StringEquals': {f'aws:ResourceTag/{self.tag_key}': [self.tag_value]}},
            ),
        ]
        return statements
