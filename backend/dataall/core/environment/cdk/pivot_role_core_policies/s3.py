from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from aws_cdk import aws_iam as iam


class S3PivotRole(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with AWS S3.
    It allows pivot role to:
    - ....
    """
    # TODO: add to corresponding module: data sharing, datasets, leave some here as base
    def get_statements(self):
        statements = [
            # Read Buckets
            iam.PolicyStatement(
                sid='ReadBuckets',
                effect=iam.Effect.ALLOW,
                actions=[
                    's3:ListAllMyBuckets',
                    's3:GetBucketLocation',
                    's3:PutBucketTagging'
                ],
                resources=['*'],
            ),
            # S3 Managed Buckets
            iam.PolicyStatement(
                sid='ManagedBuckets',
                effect=iam.Effect.ALLOW,
                actions=[
                    's3:List*',
                    's3:Delete*',
                    's3:Get*',
                    's3:Put*'
                ],
                resources=[f'arn:aws:s3:::{self.env_resource_prefix}*'],
            ),
            # S3 Imported Buckets - restrict resources via bucket policies
            iam.PolicyStatement(
                sid='ImportedBuckets',
                effect=iam.Effect.ALLOW,
                actions=[
                    's3:List*',
                    's3:GetBucket*',
                    's3:GetLifecycleConfiguration',
                    's3:GetObject',
                    's3:PutBucketPolicy',
                    's3:PutBucketTagging',
                    's3:PutObject',
                    's3:PutObjectAcl',
                    's3:PutBucketOwnershipControls',
                ],
                resources=['arn:aws:s3:::*'],
            ),
            # S3 Access points - needed for access points sharing
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
            # AWS Logging Buckets
            iam.PolicyStatement(
                sid='AWSLoggingBuckets',
                effect=iam.Effect.ALLOW,
                actions=[
                    's3:PutBucketAcl',
                    's3:PutBucketNotification'
                ],
                resources=[f'arn:aws:s3:::{self.env_resource_prefix}-logging-*'],
            ),
        ]
        return statements
