from aws_cdk import aws_iam as iam
from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet


class OmicsPolicy(PivotRoleStatementSet):
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
