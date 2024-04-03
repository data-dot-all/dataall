from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from aws_cdk import aws_iam as iam


class DashboardsPivotRole(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with AWS Quicksight.
    It allows pivot role to:
    - ....
    """

    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                sid='QuickSight',
                effect=iam.Effect.ALLOW,
                actions=[
                    'quicksight:CreateGroup',
                    'quicksight:DescribeGroup',
                    'quicksight:ListDashboards',
                    'quicksight:DescribeDataSource',
                    'quicksight:DescribeDashboard',
                    'quicksight:DescribeUser',
                    'quicksight:SearchDashboards',
                    'quicksight:GetDashboardEmbedUrl',
                    'quicksight:GenerateEmbedUrlForAnonymousUser',
                    'quicksight:GenerateEmbedUrlForRegisteredUser',
                    'quicksight:UpdateUser',
                    'quicksight:ListUserGroups',
                    'quicksight:RegisterUser',
                    'quicksight:DescribeDashboardPermissions',
                    'quicksight:UpdateDashboardPermissions',
                    'quicksight:GetAuthCode',
                    'quicksight:CreateGroupMembership',
                    'quicksight:DescribeAccountSubscription',
                    'quicksight:DescribeAccountSettings',
                ],
                resources=[
                    f'arn:aws:quicksight:*:{self.account}:group/default/*',
                    f'arn:aws:quicksight:*:{self.account}:user/default/*',
                    f'arn:aws:quicksight:*:{self.account}:datasource/*',
                    f'arn:aws:quicksight:*:{self.account}:user/*',
                    f'arn:aws:quicksight:*:{self.account}:dashboard/*',
                    f'arn:aws:quicksight:*:{self.account}:namespace/default',
                    f'arn:aws:quicksight:*:{self.account}:account/*',
                    f'arn:aws:quicksight:*:{self.account}:*',
                ],
            ),
            iam.PolicyStatement(
                sid='QuickSightSession',
                effect=iam.Effect.ALLOW,
                actions=['quicksight:GetSessionEmbedUrl'],
                resources=['*'],
            ),
        ]
        return statements
