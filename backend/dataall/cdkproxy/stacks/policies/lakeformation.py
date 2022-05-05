from aws_cdk import aws_iam as iam

from .service_policy import ServicePolicy


class LakeFormation(ServicePolicy):
    def get_statements(self):
        return [
            iam.PolicyStatement(
                actions=[
                    "lakeformation:GetDataAccess",
                    "lakeformation:GetResourceLFTags",
                    "lakeformation:ListLFTags",
                    "lakeformation:GetLFTag",
                    "lakeformation:SearchTablesByLFTags",
                    "lakeformation:SearchDatabasesByLFTags",
                    "lakeformation:GetWorkUnits",
                    "lakeformation:StartQueryPlanning",
                    "lakeformation:GetWorkUnitResults",
                    "lakeformation:GetQueryState",
                    "lakeformation:GetQueryStatistics",
                    "lakeformation:StartTransaction",
                    "lakeformation:CommitTransaction",
                    "lakeformation:CancelTransaction",
                    "lakeformation:ExtendTransaction",
                    "lakeformation:DescribeTransaction",
                    "lakeformation:ListTransactions",
                    "lakeformation:GetTableObjects",
                    "lakeformation:UpdateTableObjects",
                    "lakeformation:DeleteObjectsOnCancel",
                ],
                resources=["*"],
                effect=iam.Effect.ALLOW,
            )
        ]
