from .service_policy import ServicePolicy
from aws_cdk import aws_iam as iam


class Databrew(ServicePolicy):
    def get_statements(self):
        statements = [
            iam.PolicyStatement(actions=['databrew:List*'], resources=['*']),
            iam.PolicyStatement(
                actions=[
                    'databrew:Delete*',
                    'databrew:Describe*',
                    'databrew:PublishRecipe',
                    'databrew:SendProjectSessionAction',
                    'databrew:Start*',
                    'databrew:Stop*',
                    'databrew:TagResource',
                    'databrew:UntagResource',
                    'databrew:Update*',
                ],
                resources=[
                    f'arn:aws:databrew:{self.region}:{self.account}:*/{self.resource_prefix}*'
                ],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
            iam.PolicyStatement(
                actions=['databrew:Create*'],
                resources=['*'],
                conditions={
                    'StringEquals': {f'aws:RequestTag/{self.tag_key}': [self.tag_value]}
                },
            ),
        ]
        return statements
