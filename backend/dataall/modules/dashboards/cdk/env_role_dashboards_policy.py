from aws_cdk import aws_iam as iam

from dataall.core.environment.cdk.env_role_core_policies.service_policy import ServicePolicy
from dataall.modules.dashboards.services.dashboard_permissions import CREATE_DASHBOARD


class QuickSightPolicy(ServicePolicy):
    """
    Class including all permissions needed to work with Amazon Quicksight.
    It allows data.all users to:
    -
    """

    def get_statements(self, group_permissions, **kwargs):
        if CREATE_DASHBOARD not in group_permissions:
            return []

        return [
            iam.PolicyStatement(
                # sid="QuicksightList",
                effect=iam.Effect.ALLOW,
                actions=['quicksight:List*'],
                resources=['*'],
            ),
            iam.PolicyStatement(
                # sid="QuicksightManageTeamResources",
                effect=iam.Effect.ALLOW,
                actions=['quicksight:*'],
                resources=[
                    f'arn:aws:quicksight:{self.region}:{self.account}:*/{self.resource_prefix}-{self.team.groupUri}*'
                ],
            ),
        ]
