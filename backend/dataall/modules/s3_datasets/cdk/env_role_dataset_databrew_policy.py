from dataall.core.environment.cdk.env_role_core_policies.service_policy import ServicePolicy
from aws_cdk import aws_iam as iam

from dataall.modules.s3_datasets.services.dataset_permissions import CREATE_DATASET


class DatasetDatabrewServicePolicy(ServicePolicy):
    """
    Class including all permissions needed to work with AWS DataBrew.
    """

    def get_statements(self, group_permissions, **kwargs):
        if CREATE_DATASET not in group_permissions:
            return []

        statements = [
            iam.PolicyStatement(
                # sid="DataBrewGeneric",
                actions=['databrew:List*'],
                resources=['*'],
            ),
            iam.PolicyStatement(
                # sid="DataBrewRecipes",
                actions=[
                    'databrew:BatchDeleteRecipeVersion',
                    'databrew:*Recipe',
                ],
                resources=[f'arn:aws:databrew:{self.region}:{self.account}:recipe/{self.resource_prefix}*'],
            ),
            iam.PolicyStatement(
                # sid="DataBrewManageTeamResources",
                not_actions=[
                    'databrew:Create*',
                    'databrew:TagResource',
                    'databrew:UntagResource',
                ],
                resources=[f'arn:aws:databrew:{self.region}:{self.account}:*/{self.resource_prefix}*'],
                conditions={'StringEquals': {f'aws:ResourceTag/{self.tag_key}': [self.tag_value]}},
            ),
            iam.PolicyStatement(
                # sid="DataBrewCreateTeamResources",
                actions=[
                    'databrew:Create*',
                    'databrew:TagResource',
                ],
                resources=[f'arn:aws:databrew:{self.region}:{self.account}:*/{self.resource_prefix}*'],
                conditions={'StringEquals': {f'aws:RequestTag/{self.tag_key}': [self.tag_value]}},
            ),
        ]
        return statements
