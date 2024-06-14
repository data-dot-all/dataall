from aws_cdk import aws_iam as iam
from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet


class OmicsPolicy(PivotRoleStatementSet):
    """
    Creates an Omics policy for Pivot role accessing and interacting with Omics Projects
    """

    def get_statements(self):
        return [
            iam.PolicyStatement(
                sid='OmicsWorkflowActions',
                actions=['omics:GetWorkflow', 'omics:ListWorkflows', 'omics:StartRun', 'omics:TagResource'],
                resources=[
                    f'arn:aws:omics:{self.region}:{self.account}:workflow/*',
                    f'arn:aws:omics:{self.region}::workflow/*',
                    f'arn:aws:omics:{self.region}:{self.account}:run/*',
                ],
            ),
            iam.PolicyStatement(
                sid='OmicsRunActions',
                actions=['omics:ListRuns', 'omics:DeleteRun', 'omics:GetRun', 'omics:ListRunTasks', 'omics:CancelRun'],
                resources=[
                    f'arn:aws:omics:{self.region}:{self.account}:run/*',
                ],
            ),
            iam.PolicyStatement(
                sid='PassRoleOmics',
                actions=[
                    'iam:PassRole',
                ],
                resources=[
                    f'arn:aws:iam::{self.account}:role/{self.env_resource_prefix}*',
                ],
                conditions={
                    'StringEquals': {
                        'iam:PassedToService': [
                            'omics.amazonaws.com',
                        ]
                    }
                },
            ),
        ]
