from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from aws_cdk import aws_iam as iam


class SNSPivotRole(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with AWS SNS.
    It allows pivot role to:
    - ....
    """

    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                sid='SNSPublish',
                effect=iam.Effect.ALLOW,
                actions=[
                    'sns:Publish',
                    'sns:SetTopicAttributes',
                    'sns:GetTopicAttributes',
                    'sns:DeleteTopic',
                    'sns:Subscribe',
                    'sns:TagResource',
                    'sns:UntagResource',
                    'sns:CreateTopic',
                ],
                resources=[f'arn:aws:sns:*:{self.account}:{self.env_resource_prefix}*'],
            ),
            iam.PolicyStatement(sid='SNSList', effect=iam.Effect.ALLOW, actions=['sns:ListTopics'], resources=['*']),
        ]
        return statements
