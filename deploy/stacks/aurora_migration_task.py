from aws_cdk import aws_codebuild as codebuild, aws_iam as iam, aws_secretsmanager as secretsmanager, aws_ec2 as ec2
from constructs import Construct
from .pyNestedStack import pyNestedClass


class CodeBuildProjectStack(pyNestedClass):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        secret_id_aurora_v1_arn: str,
        secret_aurora_v2,
        kms_key_for_secret_arn: str,
        database_name: str,
        vpc_security_group: str,
        vpc,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        default_security_group = ec2.SecurityGroup.from_security_group_id(
            self, 'DefaultSecurityGroup', security_group_id=vpc.vpc_default_security_group
        )

        # Create CodeBuild project
        project = codebuild.Project(
            self,
            'PostgresMigrationProject',
            project_name='postgres-migration',
            security_groups=[vpc_security_group, default_security_group],
            vpc=vpc,
            # Define build environment
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                privileged=False,
                environment_variables={
                    'SRC_PGVER': codebuild.BuildEnvironmentVariable(
                        value='13'  # Adjust version as needed
                    ),
                    'TGT_PGVER': codebuild.BuildEnvironmentVariable(
                        value='16'  # Adjust version as needed
                    ),
                    'SRC_HOST': codebuild.BuildEnvironmentVariable(
                        type=codebuild.BuildEnvironmentVariableType.SECRETS_MANAGER,
                        value=f'{secret_id_aurora_v1_arn}:host',
                    ),
                    'SRC_PORT': codebuild.BuildEnvironmentVariable(
                        type=codebuild.BuildEnvironmentVariableType.SECRETS_MANAGER,
                        value=f'{secret_id_aurora_v1_arn}:port',
                    ),
                    'SRC_USER': codebuild.BuildEnvironmentVariable(
                        type=codebuild.BuildEnvironmentVariableType.SECRETS_MANAGER,
                        value=f'{secret_id_aurora_v1_arn}:username',
                    ),
                    'SRC_PWD': codebuild.BuildEnvironmentVariable(
                        type=codebuild.BuildEnvironmentVariableType.SECRETS_MANAGER,
                        value=f'{secret_id_aurora_v1_arn}:password',
                    ),
                    'TGT_HOST': codebuild.BuildEnvironmentVariable(
                        type=codebuild.BuildEnvironmentVariableType.SECRETS_MANAGER,
                        value=f'{secret_aurora_v2.secret_arn}:host',
                    ),
                    'TGT_PORT': codebuild.BuildEnvironmentVariable(
                        type=codebuild.BuildEnvironmentVariableType.SECRETS_MANAGER,
                        value=f'{secret_aurora_v2.secret_arn}:port',
                    ),
                    'TGT_USER': codebuild.BuildEnvironmentVariable(
                        type=codebuild.BuildEnvironmentVariableType.SECRETS_MANAGER,
                        value=f'{secret_aurora_v2.secret_arn}:username',
                    ),
                    'TGT_PWD': codebuild.BuildEnvironmentVariable(
                        type=codebuild.BuildEnvironmentVariableType.SECRETS_MANAGER,
                        value=f'{secret_aurora_v2.secret_arn}:password',
                    ),
                    'PGDATABASE': codebuild.BuildEnvironmentVariable(
                        type=codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                        value=database_name,
                    ),
                },
            ),
            # Define build specification
            build_spec=codebuild.BuildSpec.from_object(
                {
                    'version': '0.2',
                    'phases': {
                        'install': {
                            'commands': [
                                'apt install curl ca-certificates',
                                'install -d /usr/share/postgresql-common/pgdg',
                                'curl -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc --fail https://www.postgresql.org/media/keys/ACCC4CF8.asc',
                                'sh -c \'echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list\'',
                                'apt update',
                                'apt install -y postgresql-client-$SRC_PGVER postgresql-client-$TGT_PGVER',
                            ]
                        },
                        'build': {
                            'commands': [
                                'export PGHOST=$SRC_HOST PGPORT=$SRC_PORT PGUSER=$SRC_USER PGPASSWORD=$SRC_PWD',
                                '/usr/lib/postgresql/$SRC_PGVER/bin/pg_isready',
                                '/usr/lib/postgresql/$SRC_PGVER/bin/pg_dump -x -Fc -v > db.dump',
                                'export PGHOST=$TGT_HOST PGPORT=$TGT_PORT PGUSER=$TGT_USER PGPASSWORD=$TGT_PWD',
                                '/usr/lib/postgresql/$TGT_PGVER/bin/pg_isready',
                                '/usr/lib/postgresql/$TGT_PGVER/bin/pg_restore -v -x -O -C -c -d postgres db.dump',
                            ]
                        },
                    },
                }
            ),
        )

        # Add required permissions

        project.add_to_role_policy(
            iam.PolicyStatement(
                actions=['kms:Decrypt', 'kms:DescribeKey'],
                effect=iam.Effect.ALLOW,
                resources=[kms_key_for_secret_arn],
            )
        )
