from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from aws_cdk import aws_iam as iam


class DataSharingPivotRole(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with Athena
    It allows pivot role to:
    - ....
    """

    def get_statements(self):
        statements = [
            # For access point sharing and S3 bucket sharing
            iam.PolicyStatement(
                sid='IAMRolePolicy1',
                effect=iam.Effect.ALLOW,
                actions=[
                    'iam:PutRolePolicy',
                    'iam:DeleteRolePolicy',
                    'iam:AttachRolePolicy',
                    'iam:DetachRolePolicy',
                    'iam:ListAttachedRolePolicies',
                ],
                resources=[f'arn:aws:iam::{self.account}:role/*'],
            ),
            iam.PolicyStatement(
                sid='IAMRolePolicy2',
                effect=iam.Effect.ALLOW,
                actions=[
                    'iam:ListPolicyVersions',
                    'iam:CreatePolicy',
                    'iam:DeletePolicy',
                    'iam:CreatePolicyVersion',
                    'iam:DeletePolicyVersion',
                ],
                resources=[
                    f'arn:aws:iam::{self.account}:policy/{self.env_resource_prefix}*',
                    f'arn:aws:iam::{self.account}:policy/targetDatasetAccessControlPolicy',
                    f'arn:aws:iam::{self.account}:policy/dataall-targetDatasetS3Bucket-AccessControlPolicy',
                ],
            ),
            iam.PolicyStatement(
                sid='ManagedAccessPoints',
                effect=iam.Effect.ALLOW,
                actions=[
                    's3:GetAccessPoint',
                    's3:GetAccessPointPolicy',
                    's3:ListAccessPoints',
                    's3:CreateAccessPoint',
                    's3:DeleteAccessPoint',
                    's3:GetAccessPointPolicyStatus',
                    's3:DeleteAccessPointPolicy',
                    's3:PutAccessPointPolicy',
                ],
                resources=[f'arn:aws:s3:*:{self.account}:accesspoint/*'],
            ),
            # For LakeFormation named-resource sharing
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
                actions=['ram:AssociateResourceShare', 'ram:DisassociateResourceShare'],
                resources=[f'arn:aws:ram:*:{self.account}:resource-share/*'],
                conditions={'ForAllValues:StringLike': {'ram:ResourceShareName': ['LakeFormation*']}},
            ),
            iam.PolicyStatement(
                sid='RamDeleteResource',
                effect=iam.Effect.ALLOW,
                actions=['ram:DeleteResourceShare'],
                resources=[f'arn:aws:ram:*:{self.account}:resource-share/*'],
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
                actions=['ram:Get*', 'ram:List*'],
                resources=['*'],
            ),
        ]
        return statements
