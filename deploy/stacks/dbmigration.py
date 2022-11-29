from aws_cdk import aws_codebuild as codebuild
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam

from .pyNestedStack import pyNestedClass


class DBMigrationStack(pyNestedClass):
    def __init__(
        self,
        scope,
        id,
        vpc,
        envname='dev',
        resource_prefix='dataall',
        pipeline_bucket: str = None,
        tooling_account_id=None,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        self.build_project_role = iam.Role(
            self,
            id=f'DBMigrationCBRole{envname}',
            role_name=f'{resource_prefix}-{envname}-cb-dbmigration-role',
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal('codebuild.amazonaws.com'),
                iam.AccountPrincipal(tooling_account_id),
            ),
        )
        self.build_project_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    'secretsmanager:GetSecretValue',
                    'kms:Decrypt',
                    'secretsmanager:DescribeSecret',
                    'kms:Encrypt',
                    'kms:GenerateDataKey',
                    'ssm:GetParametersByPath',
                    'ssm:GetParameters',
                    'ssm:GetParameter',
                ],
                resources=[
                    f'arn:aws:secretsmanager:{self.region}:{self.account}:secret:*{resource_prefix}*',
                    f'arn:aws:secretsmanager:{self.region}:{self.account}:secret:*dataall*',
                    f'arn:aws:kms:{self.region}:{self.account}:key/*',
                    f'arn:aws:ssm:*:{self.account}:parameter/*dataall*',
                    f'arn:aws:ssm:*:{self.account}:parameter/*{resource_prefix}*',
                ],
            )
        )
        self.build_project_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    's3:GetObject',
                    's3:ListBucketVersions',
                    's3:ListBucket',
                    's3:GetBucketLocation',
                    's3:GetObjectVersion',
                    'codebuild:StartBuild',
                    'codebuild:BatchGetBuilds',
                ],
                resources=[
                    f'arn:aws:s3:::{pipeline_bucket}/*',
                    f'arn:aws:s3:::{pipeline_bucket}',
                    f'arn:aws:codebuild:{self.region}:{self.account}:project/*{resource_prefix}*',
                ],
            ),
        )
        self.build_project_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    's3:GetObject',
                    's3:ListBucketVersions',
                    's3:ListBucket',
                    's3:GetBucketLocation',
                    's3:GetObjectVersion',
                ],
                resources=[
                    f'arn:aws:s3:::{resource_prefix}-{envname}-{self.account}-{self.region}-resources/*',
                    f'arn:aws:s3:::{resource_prefix}-{envname}-{self.account}-{self.region}-resources',
                ],
            ),
        )
        self.codebuild_sg = ec2.SecurityGroup(
            self,
            f'DBMigrationCBSG{envname}',
            security_group_name=f'{resource_prefix}-{envname}-cb-dbmigration-sg',
            vpc=vpc,
            allow_all_outbound=True,
        )
        self.db_migration_project = codebuild.Project(
            scope=self,
            id=f'DBMigrationCBProject{envname}',
            project_name=f'{resource_prefix}-{envname}-dbmigration',
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
            ),
            role=self.build_project_role,
            build_spec=codebuild.BuildSpec.from_object(
                dict(
                    version='0.2',
                    phases={
                        'build': {
                            'commands': [
                                f'aws s3api get-object --bucket {pipeline_bucket} --key source_build.zip source_build.zip',
                                'unzip source_build.zip',
                                'python -m venv env',
                                '. env/bin/activate',
                                'pip install -r backend/requirements.txt',
                                'pip install alembic',
                                'export PYTHONPATH=backend',
                                f'export envname={envname}',
                                f'alembic -c backend/alembic.ini upgrade head',
                            ]
                        },
                    },
                )
            ),
            vpc=vpc,
            subnet_selection=ec2.SubnetSelection(
                subnets=vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT
                ).subnets
            ),
            security_groups=[self.codebuild_sg],
        )
