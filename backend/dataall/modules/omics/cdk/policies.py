from dataall.cdkproxy.stacks.policies.service_policy import ServicePolicy

from dataall.modules.omics.services.permissions import CREATE_OMICS_PROJECT
from dataall.modules.common.omics.cdk.statements import create_omics_statements


class OmicsPolicy(ServicePolicy):
    """
    Creates an omics policy for accessing and interacting with omics projects
    """

    def get_statements(self, group_permissions, **kwargs):
        if CREATE_OMICS_PROJECT not in group_permissions:
            return []

        return create_omics_statements(self.account, self.region, self.tag_key, self.tag_value)
