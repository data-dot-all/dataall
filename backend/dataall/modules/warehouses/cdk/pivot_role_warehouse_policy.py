from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from aws_cdk import aws_iam as iam


class WarehousesPivotRole(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with AWS Redshift.
    It allows pivot role to:
    - ....
    """
    def get_statements(self):
        statements = [
            #TODO: add necessary statements
        ]
        return statements
