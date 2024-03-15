from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from aws_cdk import aws_iam as iam


class KMSPivotRole(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with AWS KMS.
    It allows pivot role to:
    list and Describe KMS keys
    manage data.all alias KMS keys
    - ....
    """

    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                sid='KMSList',
                effect=iam.Effect.ALLOW,
                actions=[
                    'kms:List*',
                    'kms:DescribeKey',
                ],
                resources=['*'],
            ),
            iam.PolicyStatement(
                sid='KMSDataAllAlias',
                effect=iam.Effect.ALLOW,
                actions=[
                    'kms:Decrypt',
                    'kms:Encrypt',
                    'kms:GenerateDataKey*',
                    'kms:GetKeyPolicy',
                    'kms:PutKeyPolicy',
                    'kms:ReEncrypt*',
                    'kms:TagResource',
                    'kms:UntagResource',
                ],
                resources=[f'arn:aws:kms:{self.region}:{self.account}:key/*'],
                conditions={'ForAnyValue:StringLike': {'kms:ResourceAliases': [f'alias/{self.env_resource_prefix}*']}},
            ),
        ]
        return statements
