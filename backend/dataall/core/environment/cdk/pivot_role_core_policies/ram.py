from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from aws_cdk import aws_iam as iam


class RAMPivotRole(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with AWS RAM.
    It allows pivot role to:
    - ....
    """
    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                sid='RamTag',
                effect=iam.Effect.ALLOW,
                actions=['ram:TagResource'],
                resources=['*'],
                conditions={'ForAllValues:StringLike': {'ram:ResourceShareName': ['LakeFormation*']}},
            ),
            iam.PolicyStatement(
                sid='RamCreateResource',
                effect=iam.Effect.ALLOW,
                actions=['ram:CreateResourceShare'],
                resources=['*'],
                conditions={
                    'ForAllValues:StringEquals': {
                        'ram:RequestedResourceType': ['glue:Table', 'glue:Database', 'glue:Catalog']
                    }
                },
            ),
            iam.PolicyStatement(
                sid='RamUpdateResource',
                effect=iam.Effect.ALLOW,
                actions=['ram:UpdateResourceShare'],
                resources=[f'arn:aws:ram:*:{self.account}:resource-share/*'],
                conditions={
                    'ForAllValues:StringLike': {'ram:ResourceShareName': ['LakeFormation*']},
                },
            ),
            iam.PolicyStatement(
                sid='RamAssociateResource',
                effect=iam.Effect.ALLOW,
                actions=[
                    'ram:AssociateResourceShare',
                    'ram:DisassociateResourceShare'
                ],
                resources=[f'arn:aws:ram:*:{self.account}:resource-share/*'],
                conditions={'ForAllValues:StringLike': {'ram:ResourceShareName': ['LakeFormation*']}},
            ),
            iam.PolicyStatement(
                sid='RamDeleteResource',
                effect=iam.Effect.ALLOW,
                actions=['ram:DeleteResourceShare'],
                resources=[f'arn:aws:ram:*:{self.account}:resource-share/*']
            ),
            iam.PolicyStatement(
                sid='RamInvitations',
                effect=iam.Effect.ALLOW,
                actions=[
                    'ram:AcceptResourceShareInvitation',
                    'ram:RejectResourceShareInvitation',
                    'ram:EnableSharingWithAwsOrganization',
                ],
                resources=['*'],
            ),
            iam.PolicyStatement(
                sid='RamRead',
                effect=iam.Effect.ALLOW,
                actions=[
                    'ram:Get*',
                    'ram:List*'
                ],
                resources=['*'],
            )
        ]
        return statements
