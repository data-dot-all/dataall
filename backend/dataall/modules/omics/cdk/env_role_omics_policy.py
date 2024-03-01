from aws_cdk import aws_iam as iam

from dataall.core.environment.cdk.env_role_core_policies.service_policy import ServicePolicy
from dataall.modules.omics.services.omics_permissions import CREATE_OMICS_RUN


class OmicsPolicy(ServicePolicy):
    """
    Creates an Omics policy for accessing and interacting with Omics Projects
    """
    # TODO: scope down omics permissions
    # TODO: identify additional needed permissions
    # Use f'aws:ResourceTag/{self.tag_key}': [self.tag_value],
    def get_statements(self, group_permissions, **kwargs):
        if CREATE_OMICS_RUN not in group_permissions:
            return []

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
                    f'arn:aws:omics:{self.region}:{self.account}:run/{self.resource_prefix}*',
                ],
                conditions={
                    'StringEquals': {
                        f'omics:ResourceTag/{self.tag_key}': [self.tag_value]
                    },
                }
            )
        ]
