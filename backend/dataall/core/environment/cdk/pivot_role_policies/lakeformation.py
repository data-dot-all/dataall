from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from aws_cdk import aws_iam as iam


class LakeFormation(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with AWS CloudFormation.
    It allows pivot role to:
    - ....
    """
    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                sid='LakeFormation',
                effect=iam.Effect.ALLOW,
                actions=[
                    'lakeformation:UpdateResource',
                    'lakeformation:DescribeResource',
                    'lakeformation:AddLFTagsToResource',
                    'lakeformation:RemoveLFTagsFromResource',
                    'lakeformation:GetResourceLFTags',
                    'lakeformation:ListLFTags',
                    'lakeformation:CreateLFTag',
                    'lakeformation:GetLFTag',
                    'lakeformation:UpdateLFTag',
                    'lakeformation:DeleteLFTag',
                    'lakeformation:SearchTablesByLFTags',
                    'lakeformation:SearchDatabasesByLFTags',
                    'lakeformation:ListResources',
                    'lakeformation:ListPermissions',
                    'lakeformation:GrantPermissions',
                    'lakeformation:BatchGrantPermissions',
                    'lakeformation:RevokePermissions',
                    'lakeformation:BatchRevokePermissions',
                    'lakeformation:PutDataLakeSettings',
                    'lakeformation:GetDataLakeSettings',
                    'lakeformation:GetDataAccess',
                    'lakeformation:GetWorkUnits',
                    'lakeformation:StartQueryPlanning',
                    'lakeformation:GetWorkUnitResults',
                    'lakeformation:GetQueryState',
                    'lakeformation:GetQueryStatistics',
                    'lakeformation:GetTableObjects',
                    'lakeformation:UpdateTableObjects',
                    'lakeformation:DeleteObjectsOnCancel',
                ],
                resources=['*'],
            )
        ]
        return statements
