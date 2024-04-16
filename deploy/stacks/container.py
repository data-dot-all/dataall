from typing import Dict
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
from .run_if import run_if


class ContainerStack(pyNestedClass):
    def __init__(
        self,
        scope,
        id,
        vpc: ec2.Vpc = None,
        vpce_connection: ec2.Connections = None,
        envname='dev',
        resource_prefix='dataall',
        ecr_repository=None,
        image_tag=None,
        prod_sizing=False,
        pivot_role_name=None,
        tooling_account_id=None,
        s3_prefix_list=None,
        lambdas=None,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)
        self._envname = envname
        self._resource_prefix = resource_prefix

        if self.node.try_get_context('image_tag'):
            image_tag = self.node.try_get_context('image_tag')

        self._cdkproxy_image_tag = f'cdkproxy-{image_tag}'
        self._ecr_repository = ecr_repository
        self._vpc = vpc
        self._prod_sizing = prod_sizing

        (self.scheduled_tasks_sg, self.share_manager_sg) = self.create_ecs_security_groups(
            envname, resource_prefix, vpc, vpce_connection, s3_prefix_list, lambdas
        )
        self.ecs_security_groups: [aws_ec2.SecurityGroup] = [self.scheduled_tasks_sg, self.share_manager_sg]

        cluster = ecs.Cluster(
            self,
            f'{resource_prefix}-{envname}-cluster',
            cluster_name=f'{resource_prefix}-{envname}-cluster',
            vpc=vpc,
            container_insights=True,
        )

        self.task_role = self.create_task_role(envname, resource_prefix, pivot_role_name)
        self.cicd_stacks_updater_role = self.create_cicd_stacks_updater_role(
            envname, resource_prefix, tooling_account_id
        )

        cdkproxy_container_name = 'container'
        cdkproxy_log_group = self.create_log_group(envname, resource_prefix, log_group_name='cdkproxy')
        cdkproxy_image = ecs.ContainerImage.from_ecr_repository(repository=ecr_repository, tag=self._cdkproxy_image_tag)

        cdkproxy_task_definition = ecs.CfnTaskDefinition(
            self,
            f'{resource_prefix}-{envname}-cdkproxy',
            container_definitions=[
                ecs.CfnTaskDefinition.ContainerDefinitionProperty(
                    image=cdkproxy_image.image_name,
                    name=cdkproxy_container_name,
                    command=['python3.9', '-m', 'dataall.core.stacks.tasks.cdkproxy'],
                    environment=[
                        ecs.CfnTaskDefinition.KeyValuePairProperty(name='AWS_REGION', value=self.region),
                        ecs.CfnTaskDefinition.KeyValuePairProperty(name='envname', value=envname),
                        ecs.CfnTaskDefinition.KeyValuePairProperty(name='LOGLEVEL', value='DEBUG'),
                        ecs.CfnTaskDefinition.KeyValuePairProperty(name='config_location', value='/config.json'),
                    ],
                    essential=True,
                    log_configuration=ecs.CfnTaskDefinition.LogConfigurationProperty(
                        log_driver='awslogs',
                        options={
                            'awslogs-group': cdkproxy_log_group.log_group_name,
                            'awslogs-region': self.region,
                            'awslogs-stream-prefix': 'task',
                        },
                    ),
                    mount_points=[
                        ecs.CfnTaskDefinition.MountPointProperty(
                            container_path='/dataall', read_only=False, source_volume='dataall_scratch'
                        ),
                        ecs.CfnTaskDefinition.MountPointProperty(
                            container_path='/tmp', read_only=False, source_volume='dataall_tmp_scratch'
                        ),
                    ],
                    readonly_root_filesystem=True,
                )
            ],
            cpu='1024',
            memory='2048',
            execution_role_arn=self.task_role.role_arn,
            family=f'{resource_prefix}-{envname}-cdkproxy',
            requires_compatibilities=[ecs.Compatibility.FARGATE.name],
            task_role_arn=self.task_role.role_arn,
            network_mode='awsvpc',
            volumes=[
                ecs.CfnTaskDefinition.VolumeProperty(name='dataall_scratch'),
                ecs.CfnTaskDefinition.VolumeProperty(name='dataall_tmp_scratch'),
            ],
        )

        ssm.StringParameter(
            self,
            f'CDKProxyTaskDefParam{envname}',
            parameter_name=f'/dataall/{envname}/ecs/task_def_arn/cdkproxy',
            string_value=cdkproxy_task_definition.attr_task_definition_arn,
        )

        ssm.StringParameter(
            self,
            f'CDKProxyContainerParam{envname}',
            parameter_name=f'/dataall/{envname}/ecs/container/cdkproxy',
            string_value=cdkproxy_container_name,
        )

        stacks_updater, stacks_updater_task_def = self.set_scheduled_task(
            cluster=cluster,
            command=['python3.9', '-m', 'dataall.core.environment.tasks.env_stacks_updater'],
            container_id='container',
            ecr_repository=ecr_repository,
            environment=self._create_env('INFO'),
            image_tag=self._cdkproxy_image_tag,
            log_group=self.create_log_group(envname, resource_prefix, log_group_name='stacks-updater'),
            schedule_expression=Schedule.expression('cron(0 1 * * ? *)'),
            scheduled_task_id=f'{resource_prefix}-{envname}-stacks-updater-schedule',
            task_id=f'{resource_prefix}-{envname}-stacks-updater',
            task_role=self.task_role,
            vpc=vpc,
            security_group=self.scheduled_tasks_sg,
            prod_sizing=prod_sizing,
        )

        ssm.StringParameter(
            self,
            f'StacksUpdaterTaskDefParam{envname}',
            parameter_name=f'/dataall/{envname}/ecs/task_def_arn/stacks_updater',
            string_value=stacks_updater_task_def.task_definition_arn,
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
            string_value=','.join(vpc.select_subnets(subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT).subnet_ids),
        )

        self.ecs_cluster = cluster
        self.ecs_task_definitions_families = [
            cdkproxy_task_definition.family,
        ]

        self.add_catalog_indexer_task()
        self.add_sync_dataset_table_task()
        self.add_subscription_task()
        self.add_share_management_task()
        self.add_share_verifier_task()
        self.add_share_reapplier_task()

    @run_if(['modules.datasets.active', 'modules.dashboards.active'])
    def add_catalog_indexer_task(self):
        catalog_indexer_task, catalog_indexer_task_def = self.set_scheduled_task(
            cluster=self.ecs_cluster,
            command=['python3.9', '-m', 'dataall.modules.catalog.tasks.catalog_indexer_task'],
            container_id='container',
            ecr_repository=self._ecr_repository,
            environment=self._create_env('INFO'),
            image_tag=self._cdkproxy_image_tag,
            log_group=self.create_log_group(self._envname, self._resource_prefix, log_group_name='catalog-indexer'),
            schedule_expression=Schedule.expression('rate(6 hours)'),
            scheduled_task_id=f'{self._resource_prefix}-{self._envname}-catalog-indexer-schedule',
            task_id=f'{self._resource_prefix}-{self._envname}-catalog-indexer',
            task_role=self.task_role,
            vpc=self._vpc,
            security_group=self.scheduled_tasks_sg,
            prod_sizing=self._prod_sizing,
        )

        self.ecs_task_definitions_families.append(catalog_indexer_task.task_definition.family)

    @run_if(['modules.datasets.active'])
    def add_share_management_task(self):
        share_management_task_definition = ecs.FargateTaskDefinition(
            self,
            f'{self._resource_prefix}-{self._envname}-share-manager',
            cpu=1024,
            memory_limit_mib=2048,
            task_role=self.task_role,
            execution_role=self.task_role,
            family=f'{self._resource_prefix}-{self._envname}-share-manager',
        )

        share_management_container = share_management_task_definition.add_container(
            f'ShareManagementTaskContainer{self._envname}',
            container_name='container',
            image=ecs.ContainerImage.from_ecr_repository(repository=self._ecr_repository, tag=self._cdkproxy_image_tag),
            environment=self._create_env('DEBUG'),
            command=['python3.9', '-m', 'dataall.modules.dataset_sharing.tasks.share_manager_task'],
            logging=ecs.LogDriver.aws_logs(
                stream_prefix='task',
                log_group=self.create_log_group(self._envname, self._resource_prefix, log_group_name='share-manager'),
            ),
            readonly_root_filesystem=True,
        )

        ssm.StringParameter(
            self,
            f'ShareManagementTaskDef{self._envname}',
            parameter_name=f'/dataall/{self._envname}/ecs/task_def_arn/share_management',
            string_value=share_management_task_definition.task_definition_arn,
        )

        ssm.StringParameter(
            self,
            f'ShareManagementContainerParam{self._envname}',
            parameter_name=f'/dataall/{self._envname}/ecs/container/share_management',
            string_value=share_management_container.container_name,
        )
        self.ecs_task_definitions_families.append(share_management_task_definition.family)

    @run_if(['modules.datasets.active'])
    def add_share_verifier_task(self):
        verify_shares_task, verify_shares_task_def = self.set_scheduled_task(
            cluster=self.ecs_cluster,
            command=['python3.9', '-m', 'dataall.modules.dataset_sharing.tasks.share_verifier_task'],
            container_id='container',
            ecr_repository=self._ecr_repository,
            environment=self._create_env('INFO'),
            image_tag=self._cdkproxy_image_tag,
            log_group=self.create_log_group(self._envname, self._resource_prefix, log_group_name='share-verifier'),
            schedule_expression=Schedule.expression('rate(7 days)'),
            scheduled_task_id=f'{self._resource_prefix}-{self._envname}-share-verifier-schedule',
            task_id=f'{self._resource_prefix}-{self._envname}-share-verifier',
            task_role=self.task_role,
            vpc=self._vpc,
            security_group=self.scheduled_tasks_sg,
            prod_sizing=self._prod_sizing,
        )
        self.ecs_task_definitions_families.append(verify_shares_task.task_definition.family)

    @run_if(['modules.datasets.active'])
    def add_share_reapplier_task(self):
        share_reapplier_task_definition = ecs.FargateTaskDefinition(
            self,
            f'{self._resource_prefix}-{self._envname}-share-reapplier',
            cpu=1024,
            memory_limit_mib=2048,
            task_role=self.task_role,
            execution_role=self.task_role,
            family=f'{self._resource_prefix}-{self._envname}-share-reapplier',
        )

        share_reapplier_container = share_reapplier_task_definition.add_container(
            f'ShareReapplierTaskContainer{self._envname}',
            container_name='container',
            image=ecs.ContainerImage.from_ecr_repository(repository=self._ecr_repository, tag=self._cdkproxy_image_tag),
            environment=self._create_env('INFO'),
            command=['python3.9', '-m', 'dataall.modules.dataset_sharing.tasks.share_reapplier_task'],
            logging=ecs.LogDriver.aws_logs(
                stream_prefix='task',
                log_group=self.create_log_group(self._envname, self._resource_prefix, log_group_name='share-reapplier'),
            ),
            readonly_root_filesystem=True,
        )
        self.ecs_task_definitions_families.append(share_reapplier_task_definition.family)

    @run_if(['modules.datasets.active'])
    def add_subscription_task(self):
        subscriptions_task, subscription_task_def = self.set_scheduled_task(
            cluster=self.ecs_cluster,
            command=[
                'python3.9',
                '-m',
                'dataall.modules.dataset_sharing.tasks.dataset_subscription_task',
            ],
            container_id='container',
            ecr_repository=self._ecr_repository,
            environment=self._create_env('INFO'),
            image_tag=self._cdkproxy_image_tag,
            log_group=self.create_log_group(self._envname, self._resource_prefix, log_group_name='subscriptions'),
            schedule_expression=Schedule.expression('rate(15 minutes)'),
            scheduled_task_id=f'{self._resource_prefix}-{self._envname}-subscriptions-schedule',
            task_id=f'{self._resource_prefix}-{self._envname}-subscriptions',
            task_role=self.task_role,
            vpc=self._vpc,
            security_group=self.scheduled_tasks_sg,
            prod_sizing=self._prod_sizing,
        )
        self.ecs_task_definitions_families.append(subscriptions_task.task_definition.family)

    @run_if(['modules.datasets.active'])
    def add_sync_dataset_table_task(self):
        sync_tables_task, sync_tables_task_def = self.set_scheduled_task(
            cluster=self.ecs_cluster,
            command=['python3.9', '-m', 'dataall.modules.datasets.tasks.tables_syncer'],
            container_id='container',
            ecr_repository=self._ecr_repository,
            environment=self._create_env('INFO'),
            image_tag=self._cdkproxy_image_tag,
            log_group=self.create_log_group(self._envname, self._resource_prefix, log_group_name='tables-syncer'),
            schedule_expression=Schedule.expression('rate(15 minutes)'),
            scheduled_task_id=f'{self._resource_prefix}-{self._envname}-tables-syncer-schedule',
            task_id=f'{self._resource_prefix}-{self._envname}-tables-syncer',
            task_role=self.task_role,
            vpc=self._vpc,
            security_group=self.scheduled_tasks_sg,
            prod_sizing=self._prod_sizing,
        )
        self.ecs_task_definitions_families.append(sync_tables_task.task_definition.family)

    def create_ecs_security_groups(self, envname, resource_prefix, vpc, vpce_connection, s3_prefix_list, lambdas):
        scheduled_tasks_sg = ec2.SecurityGroup(
            self,
            f'ScheduledTasksSG{envname}',
            security_group_name=f'{resource_prefix}-{envname}-ecs-tasks-sg',
            vpc=vpc,
            allow_all_outbound=False,
            disable_inline_rules=True,
        )

        # Requires RAM Access via NAT
        share_manager_sg = ec2.SecurityGroup(
            self,
            f'ShareManagerSG{envname}',
            security_group_name=f'{resource_prefix}-{envname}-ecs-share-manager-tasks-sg',
            vpc=vpc,
            allow_all_outbound=False,
            disable_inline_rules=True,
        )

        for sg in [scheduled_tasks_sg, share_manager_sg]:
            sg_connection = ec2.Connections(security_groups=[sg])
            # Add ECS to VPC Endpoint Connection
            if vpce_connection:
                sg_connection.allow_to(vpce_connection, ec2.Port.tcp(443), 'Allow ECS to VPC Endpoint SG')
                sg_connection.allow_from(
                    vpce_connection,
                    ec2.Port.tcp_range(start_port=1024, end_port=65535),
                    'Allow ECS from VPC Endpoint SG',
                )
            # Add S3 Prefix List Connection
            if s3_prefix_list:
                sg_connection.allow_to(
                    ec2.Connections(peer=ec2.Peer.prefix_list(s3_prefix_list)),
                    ec2.Port.tcp(443),
                    'Allow ECS Task to S3 Prefix List',
                )

            # Add Lambda to ECS Connection
            if lambdas:
                for l in lambdas:
                    sg_connection.connections.allow_from(
                        l.connections, ec2.Port.tcp(443), 'Allow Lambda to ECS Connection'
                    )

            # Add NAT Gateway Access for Cross-region requests in same region the more specific rules apply
            sg_connection.allow_to(ec2.Peer.any_ipv4(), ec2.Port.tcp(443), 'Allow NAT Internet Access SG Egress')

        # Create SSM of Security Group IDs
        ssm.StringParameter(
            self,
            f'SecurityGroup{envname}',
            parameter_name=f'/dataall/{envname}/ecs/security_groups',
            string_value=scheduled_tasks_sg.security_group_id,
        )
        ssm.StringParameter(
            self,
            f'SecurityGroupShareManager{envname}',
            parameter_name=f'/dataall/{envname}/ecs/sharemanager_security_groups',
            string_value=share_manager_sg.security_group_id,
        )

        return scheduled_tasks_sg, share_manager_sg

    def create_cicd_stacks_updater_role(self, envname, resource_prefix, tooling_account_id):
        cicd_stacks_updater_role = iam.Role(
            self,
            id=f'StackUpdaterCBRole{envname}',
            role_name=f'{resource_prefix}-{envname}-cb-stackupdater-role',
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal('codebuild.amazonaws.com'),
                iam.AccountPrincipal(tooling_account_id),
            ),
        )
        cicd_stacks_updater_role.add_to_policy(
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
                    'iam:PassRole',
                    'ecs:RunTask',
                ],
                resources=[
                    f'arn:aws:secretsmanager:{self.region}:{self.account}:secret:*{resource_prefix}*',
                    f'arn:aws:secretsmanager:{self.region}:{self.account}:secret:*dataall*',
                    f'arn:aws:kms:{self.region}:{self.account}:key/*',
                    f'arn:aws:ssm:*:{self.account}:parameter/*dataall*',
                    f'arn:aws:ssm:*:{self.account}:parameter/*{resource_prefix}*',
                    f'arn:aws:ecs:*:{self.account}:task-definition/{resource_prefix}-{envname}-*',
                    f'arn:aws:iam::{self.account}:role/{resource_prefix}-{envname}-ecs-tasks-role',
                ],
            )
        )
        return cicd_stacks_updater_role

    def create_task_role(self, envname, resource_prefix, pivot_role_name):
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
                        f'arn:aws:iam::*:role/{pivot_role_name}*',
                        'arn:aws:iam::*:role/cdk*',
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
                iam.PolicyStatement(
                    actions=[
                        'aoss:APIAccessAll',
                    ],
                    resources=[
                        f'arn:aws:aoss:{self.region}:{self.account}:collection/*',
                    ],
                ),
            ],
        )
        task_role = iam.Role(
            self,
            f'ECSTaskRole{envname}',
            role_name=f'{resource_prefix}-{envname}-ecs-tasks-role',
            inline_policies={f'ECSRoleInlinePolicy{envname}': role_inline_policy.document},
            assumed_by=iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
        )
        task_role.grant_pass_role(task_role)
        return task_role

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
    ) -> (ecs.FargateTaskDefinition, ecs_patterns.ScheduledFargateTask):
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
            image=ecs.ContainerImage.from_ecr_repository(repository=ecr_repository, tag=image_tag),
            environment=environment,
            command=command,
            logging=ecs.LogDriver.aws_logs(stream_prefix='task', log_group=log_group),
            readonly_root_filesystem=True,
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
                subnets=vpc.select_subnets(subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT).subnets
            ),
            rule_name=scheduled_task_id,
            security_groups=[security_group],
        )
        return scheduled_task, task

    @property
    def ecs_task_role(self) -> iam.Role:
        return self.task_role

    def _create_env(self, log_lvl) -> Dict:
        return {
            'AWS_REGION': self.region,
            'envname': self._envname,
            'LOGLEVEL': log_lvl,
            'config_location': '/config.json',
        }
