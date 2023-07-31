from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from aws_cdk import aws_iam as iam


class KMS(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with AWS CloudFormation.
    It allows pivot role to:
    - ....
    """
    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                sid='KMS',
                effect=iam.Effect.ALLOW,
                actions=[
                    'kms:Decrypt',
                    'kms:Encrypt',
                    'kms:GenerateDataKey*',
                    'kms:PutKeyPolicy',
                    'kms:ReEncrypt*',
                    'kms:TagResource',
                    'kms:UntagResource',
                ],
                resources=['*'],
            ),
            iam.PolicyStatement(
                sid='KMSList',
                effect=iam.Effect.ALLOW,
                actions=[
                    'kms:List*',
                    'kms:DescribeKey',
                ],
                resources=['*'],
            ),
        ]
        return statements
