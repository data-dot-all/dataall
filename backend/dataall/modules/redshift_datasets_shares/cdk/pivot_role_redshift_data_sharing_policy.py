from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from aws_cdk import aws_iam as iam


class RedshiftDataSharingPivotRole(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to process Redshift data shares
    """

    def get_statements(self):
        statements = []
        return statements
