from aws_cdk import aws_iam as iam

from dataall.core.environment.cdk.env_role_core_policies.service_policy import ServicePolicy 
from dataall.modules.omics.services.omics_permissions import CREATE_OMICS_RUN


class OmicsPolicy(ServicePolicy):
    """
    Creates an Omics policy for accessing and interacting with Omics Projects
    """
    # TODO: scope down omics permissions
    # TODO: identify additional needed permissions
    def get_statements(self, group_permissions, **kwargs):
        if CREATE_OMICS_RUN not in group_permissions:
            return []

        return [
                iam.PolicyStatement(
                    actions=[
                    "omics:*"
                    ],
                    resources=['*'],
                ),
        ]
