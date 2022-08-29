from aws_cdk import (
    Duration,
    RemovalPolicy,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_lambda as _lambda,
    aws_ssm as ssm,
    aws_kms,
    aws_ec2,
)

from .pyNestedStack import pyNestedClass


class AuroraServerlessStack(pyNestedClass):
    def __init__(
        self,
        scope,
        id,
        envname='dev',
        resource_prefix='dataall',
        vpc: ec2.Vpc = None,
        lambdas: [_lambda.Function] = None,
        ecs_security_groups: [aws_ec2.SecurityGroup] = None,
        codebuild_dbmigration_sg: aws_ec2.SecurityGroup = None,
        prod_sizing=False,
        quicksight_monitoring_sg = None,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        db_credentials = rds.DatabaseSecret(
            self, f'{resource_prefix}-{envname}-aurora-db', username='dtaadmin'
        )

        db_subnet_group = rds.SubnetGroup(
            self,
            'DbSubnetGroup',
            description=f'{envname}db subnet group',
            subnet_group_name=f'{resource_prefix}-{envname}-db-subnet-group',
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT, one_per_az=True
                ).subnets
            ),
        )

        db_security_group = ec2.SecurityGroup(
            self,
            'AuroraSecurityGroup',
            security_group_name=f'{resource_prefix}-{envname}-aurora-sg',
            vpc=vpc,
            allow_all_outbound=False,
        )

        if lambdas:
            l: _lambda.Function
            for l in lambdas:
                sgs = l.connections.security_groups
                for i, sg in enumerate(sgs):
                    db_security_group.add_ingress_rule(
                        peer=sg,
                        connection=ec2.Port.tcp(5432),
                        description=f'Allow dataall lambda {l.function_name}',
                    )

        if ecs_security_groups:
            for sg in ecs_security_groups:
                db_security_group.add_ingress_rule(
                    peer=sg,
                    connection=ec2.Port.tcp(5432),
                    description=f'Allow dataall ECS cluster tasks',
                )

        if codebuild_dbmigration_sg:
            db_security_group.add_ingress_rule(
                peer=codebuild_dbmigration_sg,
                connection=ec2.Port.tcp(5432),
                description=f'Allow dataall ECS codebuild alembic migration',
            )

        if quicksight_monitoring_sg:
            db_security_group.add_ingress_rule(
                peer=quicksight_monitoring_sg,
                connection=ec2.Port.tcp(5432),
                description=f'Allow Quicksight connection from Quicksight to RDS port',
            )

            db_security_group.add_egress_rule(
                peer=quicksight_monitoring_sg,
                connection=ec2.Port.all_tcp(),
                description=f'Allow Quicksight connection from RDS to Quicksight',
            )

            quicksight_monitoring_sg.add_ingress_rule(
                peer=db_security_group,
                connection=ec2.Port.all_tcp(),
                description=f'Allow RDS from RDS to Quicksight',
            )

            quicksight_monitoring_sg.add_egress_rule(
                peer=db_security_group,
                connection=ec2.Port.tcp(5432),
                description=f'Allow RDS from Quicksight to RDS',
            )


        key = aws_kms.Key(
            self,
            f'AuroraKMSKey',
            removal_policy=RemovalPolicy.DESTROY
            if envname == 'dev'
            else RemovalPolicy.RETAIN,
            alias=f'{resource_prefix}-{envname}-aurora',
            enable_key_rotation=True,
        )

        database = rds.ServerlessCluster(
            self,
            f'AuroraDatabase{envname}',
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_10_18
            ),
            deletion_protection=True,
            cluster_identifier=f'{resource_prefix}-{envname}-db',
            parameter_group=rds.ParameterGroup.from_parameter_group_name(
                self, 'ParameterGroup', 'default.aurora-postgresql10'
            ),
            enable_data_api=True,
            default_database_name=f'{envname}db',
            backup_retention=Duration.days(30) if prod_sizing else None,
            subnet_group=db_subnet_group,
            vpc=vpc,
            credentials=rds.Credentials.from_secret(db_credentials),
            security_groups=[db_security_group],
            scaling=rds.ServerlessScalingOptions(
                auto_pause=Duration.days(1) if prod_sizing else Duration.minutes(10),
                max_capacity=rds.AuroraCapacityUnit.ACU_16
                if prod_sizing
                else rds.AuroraCapacityUnit.ACU_8,
                min_capacity=rds.AuroraCapacityUnit.ACU_4
                if prod_sizing
                else rds.AuroraCapacityUnit.ACU_2,
            ),
            storage_encryption_key=key,
        )
        database.add_rotation_single_user(automatically_after=Duration.days(90))
        ssm.StringParameter(
            self,
            'DatabaseHostParameter',
            parameter_name=f'/dataall/{envname}/aurora/hostname',
            string_value=str(database.cluster_endpoint.hostname),
        )
        ssm.StringParameter(
            self,
            'DatabasePortParameter',
            parameter_name=f'/dataall/{envname}/aurora/port',
            string_value=str(database.cluster_endpoint.port),
        )

        ssm.StringParameter(
            self,
            'DatabaseCredentialsArns',
            parameter_name=f'/dataall/{envname}/aurora/dbcreds',
            string_value=str(db_credentials.secret_arn),
        )

        ssm.StringParameter(
            self,
            'DatabaseDb',
            parameter_name=f'/dataall/{envname}/aurora/db',
            string_value=f'{envname}db',
        )

        ssm.StringParameter(
            self,
            'DatabaseDbKey',
            parameter_name=f'/dataall/{envname}/aurora/kms_key_id',
            string_value=key.key_id,
        )

        ssm.StringParameter(
            self,
            'DatabaseSecurityGroup',
            parameter_name=f'/dataall/{envname}/aurora/security_group_id',
            string_value=db_security_group.security_group_id,
        )

        ssm.StringParameter(
            self,
            'DatabaseResourceArn',
            parameter_name=f'/dataall/{envname}/aurora/resource_arn',
            string_value=f'arn:aws:rds:{self.region}:{self.account}:cluster:dataall{envname}db',
        )

        ssm.StringParameter(
            self,
            'DatabaseSecretArn',
            parameter_name=f'/dataall/{envname}/aurora/secret_arn',
            string_value=db_credentials.secret_arn,
        )

        self.cluster = database
        self.aurora_sg = db_security_group
