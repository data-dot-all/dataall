from aws_cdk import aws_iam as iam

from dataall.core.environment.cdk.env_role_core_policies.service_policy import ServicePolicy


class OmicsPolicy(ServicePolicy):
    """
    Creates an Omics policy for Pivot role accessing and interacting with Omics Projects
    """
    # TODO: scope down omics permissions
    # TODO: identify additional needed permissions
    # Use {self.account} --> environment account
    # Use {self.env_resource_prefix}*' --> selected prefix
    def get_statements(self):
        return [
            iam.PolicyStatement(
                actions=[
                    "omics:*"
                ],
                resources=['*'],
            ),
        ]
