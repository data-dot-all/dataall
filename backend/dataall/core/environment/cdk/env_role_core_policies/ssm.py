from .service_policy import ServicePolicy
from aws_cdk import aws_iam


class SSM(ServicePolicy):
    """
    Class including all permissions needed to work with AWS SSM Parameter Store.
    """

    def get_statements(self, group_permissions, **kwargs):
        statements = [
            aws_iam.PolicyStatement(
                # sid="SSMReadAll",
                effect=aws_iam.Effect.ALLOW,
                actions=[
                    'ssm:DescribeParameters',
                ],
                resources=['*'],
            ),
            aws_iam.PolicyStatement(
                # sid='CreateTeamParameters',
                effect=aws_iam.Effect.ALLOW,
                actions=['ssm:AddTagsToResource'],
                resources=[f'arn:aws:ssm:*:{self.account}:parameter/{self.resource_prefix}*'],
                conditions={'StringEquals': {f'aws:RequestTag/{self.tag_key}': [self.tag_value]}},
            ),
            aws_iam.PolicyStatement(
                # sid='ManageTeamParameters',
                effect=aws_iam.Effect.ALLOW,
                actions=[
                    'ssm:PutParameter',
                    'ssm:DeleteParameter',
                    'ssm:GetParameterHistory',
                    'ssm:GetParametersByPath',
                    'ssm:GetParameters',
                    'ssm:GetParameter',
                    'ssm:DeleteParameters',
                    'ssm:ListTagsForResource',
                ],
                resources=[f'arn:aws:ssm:*:{self.account}:parameter/{self.resource_prefix}*'],
                conditions={'StringEquals': {f'aws:ResourceTag/{self.tag_key}': [self.tag_value]}},
            ),
        ]
        return statements
