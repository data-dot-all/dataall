from .service_policy import ServicePolicy
from aws_cdk import aws_iam as iam


class Athena(ServicePolicy):
    """
    Class including all permissions needed to work with Amazon Athena.
    It allows data.all users to:
    - Work with team workgroup
    - Store query results in environment S3 Bucket location for the team workgroup (access to other S3 locations is restricted)
    """

    def get_statements(self, group_permissions, **kwargs):
        statements = [
            iam.PolicyStatement(
                # sid="ListAthena",
                actions=['athena:List*', 'athena:GetWorkgroup'],
                effect=iam.Effect.ALLOW,
                resources=['*'],
            ),
            iam.PolicyStatement(
                # sid="AthenaWorkgroup",
                actions=[
                    'athena:Get*',
                    'athena:BatchGet*',
                    'athena:StartQueryExecution',
                    'athena:StopQueryExecution',
                    'athena:CreateNamedQuery',
                    'athena:DeleteNamedQuery',
                    'athena:CreatePreparedStatement',
                    'athena:UpdatePreparedStatement',
                    'athena:DeletePreparedStatement',
                ],
                resources=[
                    f'arn:aws:athena:{self.region}:{self.account}:workgroup/{self.team.environmentAthenaWorkGroup}'
                ],
            ),
            iam.PolicyStatement(
                # sid="ListBucketAthena",
                actions=[
                    's3:ListBucket',
                ],
                effect=iam.Effect.ALLOW,
                resources=[f'arn:aws:s3:::{self.environment.EnvironmentDefaultBucketName}'],
                conditions={
                    'StringEquals': {
                        's3:prefix': ['', 'athenaqueries/', f'athenaqueries/{self.team.environmentIAMRoleName}/'],
                        's3:delimiter': ['/'],
                    }
                },
            ),
            iam.PolicyStatement(
                # sid="ReadWriteEnvironmentBucketAthenaQueries",
                actions=[
                    's3:PutObject',
                    's3:PutObjectAcl',
                    's3:GetObject',
                    's3:GetObjectAcl',
                    's3:GetObjectVersion',
                    's3:DeleteObject',
                ],
                resources=[
                    f'arn:aws:s3:::{self.environment.EnvironmentDefaultBucketName}/athenaqueries/{self.team.environmentIAMRoleName}/*'
                ],
                effect=iam.Effect.ALLOW,
            ),
        ]
        return statements
