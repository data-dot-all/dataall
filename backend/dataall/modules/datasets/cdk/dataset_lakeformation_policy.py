from aws_cdk import aws_iam as iam

from dataall.base.cdkproxy.stacks.policies.service_policy import ServicePolicy
from dataall.modules.datasets.services.dataset_permissions import CREATE_DATASET


class DatasetLakeFormationServicePolicy(ServicePolicy):
    def get_statements(self, group_permissions, **kwargs):
        if CREATE_DATASET not in group_permissions:
            return []

        return [
            iam.PolicyStatement(
                actions=[
                    'lakeformation:GetDataAccess',
                    'lakeformation:GetResourceLFTags',
                    'lakeformation:ListLFTags',
                    'lakeformation:GetLFTag',
                    'lakeformation:SearchTablesByLFTags',
                    'lakeformation:SearchDatabasesByLFTags',
                    'lakeformation:GetWorkUnits',
                    'lakeformation:StartQueryPlanning',
                    'lakeformation:GetWorkUnitResults',
                    'lakeformation:GetQueryState',
                    'lakeformation:GetQueryStatistics',
                    'lakeformation:StartTransaction',
                    'lakeformation:CommitTransaction',
                    'lakeformation:CancelTransaction',
                    'lakeformation:ExtendTransaction',
                    'lakeformation:DescribeTransaction',
                    'lakeformation:ListTransactions',
                    'lakeformation:GetTableObjects',
                    'lakeformation:UpdateTableObjects',
                    'lakeformation:DeleteObjectsOnCancel',
                ],
                resources=['*'],
                effect=iam.Effect.ALLOW,
            )
        ]
