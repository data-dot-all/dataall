from aws_cdk import aws_iam as iam

from .service_policy import ServicePolicy


class QuickSight(ServicePolicy):
    def get_statements(self):
        return [
            iam.PolicyStatement(
                sid="QuicksightRead",
                effect=iam.Effect.ALLOW,
                actions=[
                    'quicksight:ListDataSets',
                    'quicksight:CreateDataSource',
                    'quicksight:SetGroupMapping',
                    'quicksight:SearchDirectoryGroups',
                    'quicksight:ListIngestions',
                    'quicksight:GetAnonymousUserEmbedUrl',
                    'quicksight:ListDataSources',
                    'quicksight:GetSessionEmbedUrl',
                    'quicksight:GetGroupMapping',
                    'quicksight:ListNamespaces',
                ],
                resources=['*'],
            ),
            iam.PolicyStatement(
                sid="QuicksightManageTeamResources",
                effect=iam.Effect.ALLOW,
                actions=[
                    'quicksight:*',
                ],
                resources=[
                    f'arn:aws:quicksight:{self.region}:{self.account}:analysis/{self.resource_prefix}-{self.team.groupUri}*',
                    f'arn:aws:quicksight:{self.region}:{self.account}:folder/{self.resource_prefix}-{self.team.groupUri}*',
                    f'arn:aws:quicksight:{self.region}:{self.account}:dataset/{self.resource_prefix}-{self.team.groupUri}*/ingestion/*',
                    f'arn:aws:quicksight:{self.region}:{self.account}:customization/{self.resource_prefix}-{self.team.groupUri}*',
                    f'arn:aws:quicksight:{self.region}:{self.account}:dashboard/{self.resource_prefix}-{self.team.groupUri}*',
                    f'arn:aws:quicksight:{self.region}:{self.account}:datasource/{self.resource_prefix}-{self.team.groupUri}*',
                    f'arn:aws:quicksight:{self.region}:{self.account}:template/{self.resource_prefix}-{self.team.groupUri}*',
                    f'arn:aws:quicksight:{self.region}:{self.account}:theme/{self.resource_prefix}-{self.team.groupUri}*',
                ],
            ),
        ]
