from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_iam as iam,
    aws_ssm as ssm,
    aws_ec2,
    aws_logs as logs,
    RemovalPolicy,
)
from aws_cdk.aws_applicationautoscaling import Schedule

from .pyNestedStack import pyNestedClass


class ContainerStack(pyNestedClass):
    def __init__(
        self,
        scope,
        id,
        vpc: ec2.Vpc = None,
        vpc_endpoints_sg: ec2.SecurityGroup = None,
        envname='dev',
        resource_prefix='dataall',
        ecr_repository=None,
        image_tag=None,
        prod_sizing=False,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        if self.node.try_get_context('image_tag'):
            image_tag = self.node.try_get_context('image_tag')

        cdkproxy_image_tag = f'cdkproxy-{image_tag}'

        self.ecs_security_groups: [aws_ec2.SecurityGroup] = []

        cluster = ecs.Cluster(
            self,
            f'{resource_prefix}-{envname}-cluster',
            cluster_name=f'{resource_prefix}-{envname}-cluster',
            vpc=vpc,
            container_insights=True,
        )

        task_role = self.create_task_role(envname, resource_prefix)

        cdkproxy_task_definition = ecs.FargateTaskDefinition(
            self,
            f'{resource_prefix}-{envname}-cdkproxy',
            cpu=1024,
            memory_limit_mib=2048,
            task_role=task_role,
            execution_role=task_role,
            family=f'{resource_prefix}-{envname}-cdkproxy',
        )

        cdkproxy_container = cdkproxy_task_definition.add_container(
            f'ShareManagementTaskContainer{envname}',
            container_name=f'container',
            image=ecs.ContainerImage.from_ecr_repository(
                repository=ecr_repository, tag=cdkproxy_image_tag
            ),
            environment={
                'AWS_REGION': self.region,
                'envname': envname,
                'LOGLEVEL': 'DEBUG',
            },
            command=['python3.8', '-m', 'dataall.tasks.cdkproxy'],
            logging=ecs.LogDriver.aws_logs(
                stream_prefix='task',
                log_group=self.create_log_group(
                    envname, resource_prefix, log_group_name='cdkproxy'
                ),
            ),
        )

        ssm.StringParameter(
            self,
            f'CDKProxyTaskDefParam{envname}',
            parameter_name=f'/dataall/{envname}/ecs/task_def_arn/cdkproxy',
            string_value=cdkproxy_task_definition.task_definition_arn,
        )

        ssm.StringParameter(
            self,
            f'CDKProxyContainerParam{envname}',
            parameter_name=f'/dataall/{envname}/ecs/container/cdkproxy',
            string_value=cdkproxy_container.container_name,
        )

        scheduled_tasks_sg = self.create_task_sg(
            envname, resource_prefix, vpc, vpc_endpoints_sg
        )

        sync_tables_task = self.set_scheduled_task(
            cluster=cluster,
            command=['python3.8', '-m', 'dataall.tasks.tables_syncer'],
            container_id=f'container',
            ecr_repository=ecr_repository,
            environment={
                'AWS_REGION': self.region,
                'envname': envname,
                'LOGLEVEL': 'INFO',
            },
            image_tag=cdkproxy_image_tag,
            log_group=self.create_log_group(
                envname, resource_prefix, log_group_name='tables-syncer'
            ),
            schedule_expression=Schedule.expression('rate(15 minutes)'),
            scheduled_task_id=f'{resource_prefix}-{envname}-tables-syncer-schedule',
            task_id=f'{resource_prefix}-{envname}-tables-syncer',
            task_role=task_role,
            vpc=vpc,
            security_group=scheduled_tasks_sg,
            prod_sizing=prod_sizing,
        )
        self.ecs_security_groups.extend(sync_tables_task.task.security_groups)

        catalog_indexer_task = self.set_scheduled_task(
            cluster=cluster,
            command=['python3.8', '-m', 'dataall.tasks.catalog_indexer'],
            container_id=f'container',
            ecr_repository=ecr_repository,
            environment={
                'AWS_REGION': self.region,
                'envname': envname,
                'LOGLEVEL': 'INFO',
            },
            image_tag=cdkproxy_image_tag,
            log_group=self.create_log_group(
                envname, resource_prefix, log_group_name='catalog-indexer'
            ),
            schedule_expression=Schedule.expression('rate(6 hours)'),
            scheduled_task_id=f'{resource_prefix}-{envname}-catalog-indexer-schedule',
            task_id=f'{resource_prefix}-{envname}-catalog-indexer',
            task_role=task_role,
            vpc=vpc,
            security_group=scheduled_tasks_sg,
            prod_sizing=prod_sizing,
        )
        self.ecs_security_groups.extend(catalog_indexer_task.task.security_groups)

        stacks_updater = self.set_scheduled_task(
            cluster=cluster,
            command=['python3.8', '-m', 'dataall.tasks.stacks_updater'],
            container_id=f'container',
            ecr_repository=ecr_repository,
            environment={
                'AWS_REGION': self.region,
                'envname': envname,
                'LOGLEVEL': 'INFO',
            },
            image_tag=cdkproxy_image_tag,
            log_group=self.create_log_group(
                envname, resource_prefix, log_group_name='stacks-updater'
            ),
            schedule_expression=Schedule.expression('cron(0 1 * * ? *)'),
            scheduled_task_id=f'{resource_prefix}-{envname}-stacks-updater-schedule',
            task_id=f'{resource_prefix}-{envname}-stacks-updater',
            task_role=task_role,
            vpc=vpc,
            security_group=scheduled_tasks_sg,
            prod_sizing=prod_sizing,
        )
        self.ecs_security_groups.extend(stacks_updater.task.security_groups)

        update_bucket_policies_task = self.set_scheduled_task(
            cluster=cluster,
            command=['python3.8', '-m', 'dataall.tasks.bucket_policy_updater'],
            container_id=f'container',
            ecr_repository=ecr_repository,
            environment={
                'AWS_REGION': self.region,
                'envname': envname,
                'LOGLEVEL': 'INFO',
            },
            image_tag=cdkproxy_image_tag,
            log_group=self.create_log_group(
                envname, resource_prefix, log_group_name='policies-updater'
            ),
            schedule_expression=Schedule.expression('rate(15 minutes)'),
            scheduled_task_id=f'{resource_prefix}-{envname}-policies-updater-schedule',
            task_id=f'{resource_prefix}-{envname}-policies-updater',
            task_role=task_role,
            vpc=vpc,
            security_group=scheduled_tasks_sg,
            prod_sizing=prod_sizing,
        )
        self.ecs_security_groups.extend(
            update_bucket_policies_task.task.security_groups
        )

        subscriptions_task = self.set_scheduled_task(
            cluster=cluster,
            command=[
                'python3.8',
                '-m',
                'dataall.tasks.subscriptions.subscription_service',
            ],
            container_id=f'container',
            ecr_repository=ecr_repository,
            environment={
                'AWS_REGION': self.region,
                'envname': envname,
                'LOGLEVEL': 'INFO',
            },
            image_tag=cdkproxy_image_tag,
            log_group=self.create_log_group(
                envname, resource_prefix, log_group_name='subscriptions'
            ),
            schedule_expression=Schedule.expression('rate(15 minutes)'),
            scheduled_task_id=f'{resource_prefix}-{envname}-subscriptions-schedule',
            task_id=f'{resource_prefix}-{envname}-subscriptions',
            task_role=task_role,
            vpc=vpc,
            security_group=scheduled_tasks_sg,
            prod_sizing=prod_sizing,
        )
        self.ecs_security_groups.extend(subscriptions_task.task.security_groups)

        share_management_task_definition = ecs.FargateTaskDefinition(
            self,
            f'{resource_prefix}-{envname}-share-manager',
            cpu=1024,
            memory_limit_mib=2048,
            task_role=task_role,
            execution_role=task_role,
            family=f'{resource_prefix}-{envname}-share-manager',
        )

        share_management_container = share_management_task_definition.add_container(
            f'ShareManagementTaskContainer{envname}',
            container_name=f'container',
            image=ecs.ContainerImage.from_ecr_repository(
                repository=ecr_repository, tag=cdkproxy_image_tag
            ),
            environment={
                'AWS_REGION': self.region,
                'envname': envname,
                'LOGLEVEL': 'DEBUG',
            },
            command=['python3.8', '-m', 'dataall.tasks.share_manager'],
            logging=ecs.LogDriver.aws_logs(
                stream_prefix='task',
                log_group=self.create_log_group(
                    envname, resource_prefix, log_group_name='share-manager'
                ),
            ),
        )

        ssm.StringParameter(
            self,
            f'ShareManagementTaskDef{envname}',
            parameter_name=f'/dataall/{envname}/ecs/task_def_arn/share_management',
            string_value=share_management_task_definition.task_definition_arn,
        )

        ssm.StringParameter(
            self,
            f'ShareManagementContainerParam{envname}',
            parameter_name=f'/dataall/{envname}/ecs/container/share_management',
            string_value=share_management_container.container_name,
        )

        ssm.StringParameter(
            self,
            f'ECSClusterNameParam{envname}',
            parameter_name=f'/dataall/{envname}/ecs/cluster/name',
            string_value=cluster.cluster_name,
        )

        ssm.StringParameter(
            self,
            f'VPCPrivateSubnetsParam{envname}',
            parameter_name=f'/dataall/{envname}/ecs/private_subnets',
            string_value=','.join(
                vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT
                ).subnet_ids
            ),
        )

        ssm.StringParameter(
            self,
            f'SecurityGroup{envname}',
            parameter_name=f'/dataall/{envname}/ecs/security_groups',
            string_value=','.join(
                [s.security_group_id for s in sync_tables_task.task.security_groups]
            ),
        )

        self.ecs_cluster = cluster
        self.ecs_task_definitions = [
            cdkproxy_task_definition,
            sync_tables_task.task_definition,
            update_bucket_policies_task.task_definition,
            catalog_indexer_task.task_definition,
            share_management_task_definition,
            subscriptions_task.task_definition,
        ]

    def create_task_role(self, envname, resource_prefix):
        role_inline_policy = iam.Policy(
            self,
            f'ECSRolePolicy{envname}',
            policy_name=f'{resource_prefix}-{envname}-ecs-tasks-policy',
            statements=[
                iam.PolicyStatement(
                    actions=[
                        'secretsmanager:GetSecretValue',
                        'kms:Decrypt',
                        'secretsmanager:DescribeSecret',
                        'ecs:RunTask',
                        'kms:Encrypt',
                        'ecs:ListTasks',
                        'sqs:ReceiveMessage',
                        'kms:GenerateDataKey',
                        'sqs:SendMessage',
                        'ecs:DescribeClusters',
                        'ssm:GetParametersByPath',
                        'ssm:GetParameters',
                        'ssm:GetParameter',
                        'sns:Publish',
                        'sns:Subscribe',
                    ],
                    resources=[
                        f'arn:aws:secretsmanager:{self.region}:{self.account}:secret:*{resource_prefix}*',
                        f'arn:aws:secretsmanager:{self.region}:{self.account}:secret:*dataall*',
                        f'arn:aws:ecs:{self.region}:{self.account}:cluster/*{resource_prefix}*',
                        f'arn:aws:ecs:{self.region}:{self.account}:container-instance/*{resource_prefix}*/*',
                        f'arn:aws:ecs:{self.region}:{self.account}:task-definition/*{resource_prefix}*:*',
                        f'arn:aws:kms:{self.region}:{self.account}:key/*',
                        f'arn:aws:sqs:{self.region}:{self.account}:*{resource_prefix}*',
                        f'arn:aws:ssm:*:{self.account}:parameter/*dataall*',
                        f'arn:aws:ssm:*:{self.account}:parameter/*{resource_prefix}*',
                        f'arn:aws:sns:{self.region}:{self.account}:*{resource_prefix}*',
                    ],
                ),
                iam.PolicyStatement(
                    actions=[
                        'sts:AssumeRole',
                    ],
                    resources=[
                        f"arn:aws:iam::*:role/{self.node.try_get_context('pivot_role_name') or 'dataallPivotRole'}",
                        f'arn:aws:iam::*:role/cdk*',
                        'arn:aws:iam::*:role/ddk*',
                        f'arn:aws:iam::{self.account}:role/{resource_prefix}-{envname}-ecs-tasks-role',
                    ],
                ),
                iam.PolicyStatement(
                    actions=[
                        'ecs:ListTasks',
                    ],
                    resources=['*'],
                ),
                iam.PolicyStatement(
                    actions=[
                        's3:GetObject',
                        's3:ListBucketVersions',
                        's3:ListBucket',
                        's3:GetBucketLocation',
                        's3:GetObjectVersion',
                        'logs:StartQuery',
                        'logs:DescribeLogGroups',
                        'logs:DescribeLogStreams',
                        'logs:PutLogEvents',
                        'logs:CreateLogStream',
                    ],
                    resources=[
                        f'arn:aws:s3:::{resource_prefix}-{envname}-{self.account}-{self.region}-resources/*',
                        f'arn:aws:s3:::{resource_prefix}-{envname}-{self.account}-{self.region}-resources',
                        f'arn:aws:logs:{self.region}:{self.account}:log-group:*{resource_prefix}*:log-stream:*',
                        f'arn:aws:logs:{self.region}:{self.account}:log-group:*{resource_prefix}*',
                    ],
                ),
                iam.PolicyStatement(
                    actions=[
                        'ec2:Describe*',
                    ],
                    resources=['*'],
                ),
            ],
        )
        task_role = iam.Role(
            self,
            f'ECSTaskRole{envname}',
            role_name=f'{resource_prefix}-{envname}-ecs-tasks-role',
            inline_policies={
                f'ECSRoleInlinePolicy{envname}': role_inline_policy.document
            },
            assumed_by=iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
        )
        task_role.grant_pass_role(task_role)
        return task_role

    def create_task_sg(self, envname, resource_prefix, vpc, vpc_endpoints_sg):
        if vpc_endpoints_sg:
            scheduled_tasks_sg = ec2.SecurityGroup(
                self,
                f'ScheduledTasksSG{envname}',
                security_group_name=f'{resource_prefix}-{envname}-ecs-tasks-sg',
                vpc=vpc,
                allow_all_outbound=False,
            )

            scheduled_tasks_sg.add_egress_rule(
                peer=vpc_endpoints_sg,
                connection=ec2.Port.tcp(443),
                description='Allow VPC Endpoint SG Egress',
            )
        else:
            scheduled_tasks_sg = ec2.SecurityGroup(
                self,
                f'ScheduledTasksSG{envname}',
                security_group_name=f'{resource_prefix}-{envname}-ecs-tasks-sg',
                vpc=vpc,
                allow_all_outbound=True,
            )
        return scheduled_tasks_sg

    def create_log_group(self, envname, resource_prefix, log_group_name):
        log_group = logs.LogGroup(
            self,
            f'ECSLogGroup{log_group_name}{envname}',
            log_group_name=f'/{resource_prefix}/{envname}/ecs/{log_group_name}',
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY,
        )
        return log_group

    @staticmethod
    def allow_alb_access(alb, ip_ranges, vpc):
        if ip_ranges:
            for ip_range in ip_ranges:
                alb.load_balancer.connections.allow_from(
                    ec2.Peer.ipv4(ip_range),
                    ec2.Port.tcp(443),
                    'Allow inbound HTTPS',
                )
                for sg in alb.service.connections.security_groups:
                    sg.connections.allow_from(
                        ec2.Peer.ipv4(ip_range),
                        ec2.Port.tcp(443),
                        'Allow inbound HTTPS',
                    )
        else:
            alb.load_balancer.connections.allow_from(
                ec2.Peer.ipv4(vpc.vpc_cidr_block),
                ec2.Port.tcp(443),
                'Allow inbound HTTPS',
            )
            for sg in alb.service.connections.security_groups:
                sg.connections.allow_from(
                    ec2.Peer.ipv4(vpc.vpc_cidr_block),
                    ec2.Port.tcp(443),
                    'Allow inbound HTTPS',
                )

    def set_scheduled_task(
        self,
        cluster,
        command,
        container_id,
        ecr_repository,
        environment,
        image_tag,
        log_group,
        schedule_expression,
        scheduled_task_id,
        task_id,
        task_role,
        vpc,
        security_group,
        prod_sizing,
    ) -> ecs_patterns.ScheduledFargateTask:
        task = ecs.FargateTaskDefinition(
            self,
            task_id,
            family=task_id,
            cpu=1024,
            memory_limit_mib=2048,
            task_role=task_role,
            execution_role=task_role,
        )
        task.add_container(
            container_id,
            container_name=container_id,
            image=ecs.ContainerImage.from_ecr_repository(
                repository=ecr_repository, tag=image_tag
            ),
            environment=environment,
            command=command,
            logging=ecs.LogDriver.aws_logs(stream_prefix='task', log_group=log_group),
        )
        scheduled_task = ecs_patterns.ScheduledFargateTask(
            self,
            scheduled_task_id,
            cluster=cluster,
            schedule=schedule_expression,
            scheduled_fargate_task_definition_options=ecs_patterns.ScheduledFargateTaskDefinitionOptions(
                task_definition=task
            ),
            vpc=vpc,
            subnet_selection=ec2.SubnetSelection(
                subnets=vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT
                ).subnets
            ),
            rule_name=scheduled_task_id
            # security_groups=[security_group],
        )
        return scheduled_task
