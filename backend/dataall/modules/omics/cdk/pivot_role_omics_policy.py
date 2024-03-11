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
                actions=[
                    "omics:ListWorkflows",
                    "omics:GetWorkflow"
                ],
                resources=[
                    f'arn:aws:omics:{self.region}:{self.account}:workflow/*'
                ]
            ),
            iam.PolicyStatement(
                sid='OmicsRunActions',
                actions=[
                    "omics:StartRun",
                    "omics:ListRuns",
                    "omics:DeleteRun",
                    "omics:GetRun",
                    "omics:ListRunTasks",
                    "omics:CancelRun"
                ],
                resources=[
                    f'arn:aws:omics:{self.region}:{self.account}:run/{self.env_resource_prefix}*',
                ]
            )
        ]
