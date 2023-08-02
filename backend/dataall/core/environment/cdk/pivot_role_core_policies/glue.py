from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from aws_cdk import aws_iam as iam


class GluePivotRole(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with AWS Glue.
    It allows pivot role to:
    - ....
    """
    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                sid='GlueCatalog',
                effect=iam.Effect.ALLOW,
                actions=[
                    'glue:BatchCreatePartition',
                    'glue:BatchDeletePartition',
                    'glue:BatchDeleteTable',
                    'glue:CreateDatabase',
                    'glue:CreatePartition',
                    'glue:CreateTable',
                    'glue:DeleteDatabase',
                    'glue:DeletePartition',
                    'glue:DeleteTable',
                    'glue:BatchGet*',
                    'glue:Get*',
                    'glue:List*',
                    'glue:SearchTables',
                    'glue:UpdateDatabase',
                    'glue:UpdatePartition',
                    'glue:UpdateTable',
                    'glue:TagResource',
                    'glue:DeleteResourcePolicy',
                    'glue:PutResourcePolicy',
                ],
                resources=['*'],
            ),
            # Glue ETL - needed to start crawler and profiling jobs
            iam.PolicyStatement(
                sid='GlueETL',
                effect=iam.Effect.ALLOW,
                actions=[
                    'glue:StartCrawler',
                    'glue:StartJobRun',
                    'glue:StartTrigger',
                    'glue:UpdateTrigger',
                    'glue:UpdateJob',
                    'glue:UpdateCrawler',
                ],
                resources=[
                    f'arn:aws:glue:*:{self.account}:crawler/{self.env_resource_prefix}*',
                    f'arn:aws:glue:*:{self.account}:job/{self.env_resource_prefix}*',
                    f'arn:aws:glue:*:{self.account}:trigger/{self.env_resource_prefix}*',
                ],
            )
        ]
        return statements
