from aws_cdk import aws_iam as iam

from .service_policy import ServicePolicy


class QuickSight(ServicePolicy):
    """
    Class including all permissions needed to work with Amazon Quicksight.
    It allows data.all users to:
    -
    """
    def get_statements(self):
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
