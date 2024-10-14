from dataall.core.environment.cdk.pivot_role_stack import PivotRoleStatementSet
from aws_cdk import aws_iam as iam


class S3PivotRole(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with AWS S3.
    It allows pivot role to:
    - ....
    """

    def get_statements(self):
        statements = [
            # Read Buckets
            iam.PolicyStatement(
                sid='ReadBuckets',
                effect=iam.Effect.ALLOW,
                actions=[
                    's3:ListAllMyBuckets',
                    's3:ListAccessPoints',
                    's3:GetBucketLocation',
                    's3:PutBucketTagging',
                    's3:GetEncryptionConfiguration',
                ],
                resources=['*'],
            ),
            # S3 Managed Buckets
            iam.PolicyStatement(
                sid='ManagedBuckets',
                effect=iam.Effect.ALLOW,
                actions=['s3:List*', 's3:Delete*', 's3:Get*', 's3:Put*'],
                resources=[f'arn:aws:s3:::{self.env_resource_prefix}*'],
            ),
            # AWS Logging Buckets
            iam.PolicyStatement(
                sid='AWSLoggingBuckets',
                effect=iam.Effect.ALLOW,
                actions=['s3:PutBucketAcl', 's3:PutBucketNotification'],
                resources=[f'arn:aws:s3:::{self.env_resource_prefix}-logging-*'],
            ),
        ]
        return statements
