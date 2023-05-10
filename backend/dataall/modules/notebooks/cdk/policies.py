from dataall.cdkproxy.stacks.policies.service_policy import ServicePolicy

from dataall.modules.notebooks.services.notebook_permissions import CREATE_NOTEBOOK
from dataall.modules.sagemaker_base.cdk.statements import create_sagemaker_statements


class SagemakerPolicy(ServicePolicy):
    """
    Creates a sagemaker policy for accessing and interacting with SageMaker notebooks
    """

    def get_statements(self, group_permissions, **kwargs):
        if CREATE_NOTEBOOK not in group_permissions:
            return []

        return create_sagemaker_statements(self.account, self.region, self.tag_key, self.tag_value)
