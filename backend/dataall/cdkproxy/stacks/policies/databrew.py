from .service_policy import ServicePolicy
from aws_cdk import aws_iam as iam


class Databrew(ServicePolicy):
    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                sid="DataBrewListAll",
                actions=['databrew:List*'],
                resources=['*']
            ),
            iam.PolicyStatement(
                sid="DataBrewManageTeamResources",
                actions=[
                    'databrew:Delete*',
                    'databrew:Describe*',
                    'databrew:Update*',
                    'databrew:Start*',
                    'databrew:Stop*',
                    'databrew:PublishRecipe',
                    'databrew:SendProjectSessionAction',
                    'databrew:BatchDeleteRecipeVersion',
                    'databrew:TagResource',
                    'databrew:UntagResource',
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
                sid="DataBrewCreateTeamResources",
                actions=['databrew:Create*'],
                resources=[
                    f'arn:aws:databrew:{self.region}:{self.account}:*/{self.resource_prefix}*'
                ],
                conditions={
                    'StringEquals': {f'aws:RequestTag/{self.tag_key}': [self.tag_value]}
                },
            ),
        ]
        return statements
