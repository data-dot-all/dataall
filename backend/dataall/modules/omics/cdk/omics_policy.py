from dataall.cdkproxy.stacks.policies.service_policy import ServicePolicy

from dataall.modules.omics.services.permissions import CREATE_OMICS_RUN
from dataall.modules.common.omics.cdk.statements import create_omics_statements


class OmicsPolicy(ServicePolicy):
    """
    Creates an Omics policy for accessing and interacting with Omics Projects
    """

    def get_statements(self, group_permissions, **kwargs):
        if CREATE_OMICS_RUN not in group_permissions:
            return [
                ## TODO: add list of policies to attach to IAM role for team roles
            ]

        return create_omics_statements(self.account, self.region, self.tag_key, self.tag_value)
