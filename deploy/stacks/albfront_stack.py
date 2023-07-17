from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_iam as iam,
    aws_ecr as ecr,
    aws_logs as logs,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_elasticloadbalancing as elb,
    aws_s3 as s3,
    Stack,
    Duration,
    RemovalPolicy,
    Fn,
)


class AlbFrontStack(Stack):
    def __init__(
        self,
        scope,
        id,
        envname='dev',
        resource_prefix='dataall',
        ecr_repository=None,
        image_tag=None,
        custom_domain=None,
        ip_ranges=None,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        if self.node.try_get_context('image_tag'):
            image_tag = self.node.try_get_context('image_tag')

        frontend_image_tag = f'frontend-{image_tag}'
        userguide_image_tag = f'userguide-{image_tag}'

        vpc = ec2.Vpc.from_vpc_attributes(
            self,
            'vpc',
            vpc_id=Fn.import_value(f'{resource_prefix}-{envname}-vpcId'),
            availability_zones=[self.availability_zones[0]],
            private_subnet_ids=[
                Fn.import_value(f'{resource_prefix}-{envname}-privateSubnet-1'),
                Fn.import_value(f'{resource_prefix}-{envname}-privateSubnet-2'),
            ],
            vpc_cidr_block=Fn.import_value(f'{resource_prefix}-{envname}-cidrBlock'),
        )

        cluster = ecs.Cluster.from_cluster_attributes(
            self,
            f'{resource_prefix}-{envname}-cluster',
            cluster_name=f'{resource_prefix}-{envname}-cluster',
            vpc=vpc,
            security_groups=[],
        )

        ecr_repository = ecr.Repository.from_repository_arn(
            self, 'EcrRepository', repository_arn=ecr_repository
        )

        role_inline_policy = iam.Policy(
            self,
            f'EcsRolePolicy{envname}',
            policy_name=f'{resource_prefix}-{envname}-ecs-albtasks-policy',
            statements=[
                iam.PolicyStatement(
                    actions=[
                        'sts:AssumeRole',
                        'sns:Publish',
                        'sns:Subscribe',
                        'sqs:SendMessage',
                        'sqs:ReceiveMessage',
                        'iam:PassRole',
                        'iam:ListRoles',
                        'kms:Decrypt',
                        'kms:Encrypt',
                        'kms:GenerateDataKey',
                        'secretsmanager:GetSecretValue',
                        'secretsmanager:DescribeSecret',
                        'ssm:GetParametersByPath',
                        'ssm:GetParameters',
                        'ssm:GetParameter',
                        'ec2:Describe*',
                        'ecs:RunTask',
                        'ecs:DescribeClusters',
                        'ecs:DescribeTasks',
                        'ecs:ListTasks',
                        'organizations:DescribeOrganization',
                        'logs:Describe*',
                        'logs:Get*',
                        'logs:List*',
                        'logs:CreateLogStream',
                        'logs:PutLogEvents',
                    ],
                    resources=['*'],
                ),
            ],
        )

        task_role = iam.Role(
            self,
            f'ECSTaskRole{envname}',
            role_name=f'{resource_prefix}-{envname}-ecs-albtasks-role',
            inline_policies={
                f'EcsRoleInlinePolicy{envname}': role_inline_policy.document
            },
            assumed_by=iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
        )

        task_role.grant_pass_role(task_role)

        logs_bucket = s3.Bucket(
            self,
            f'{resource_prefix}-{envname}-elb-access-logs',
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            server_access_logs_bucket=s3.Bucket.from_bucket_name(
                self,
                f'AccessLogsBucket',
                Fn.import_value(f'{resource_prefix}-{envname}-access-logs-bucket-name'),
            ),
            server_access_logs_prefix=f'elb_access_logs',
            versioned=True,
            auto_delete_objects=True,
        )
        logs_bucket.grant_put(iam.ServicePrincipal('delivery.logs.amazonaws.com'))
        logs_bucket.grant_read(iam.ServicePrincipal('delivery.logs.amazonaws.com'))

        frontend_alternate_domain = custom_domain['hosted_zone_name']
        userguide_alternate_domain = 'userguide.' + custom_domain['hosted_zone_name']

        hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
            self,
            'CustomDomainHostedZone',
            hosted_zone_id=custom_domain['hosted_zone_id'],
            zone_name=custom_domain['hosted_zone_name'],
        )

        if custom_domain and custom_domain.get('certificate_arn'):
            certificate = acm.Certificate.from_certificate_arn(self, "CustomDomainCertificate",
                                                               custom_domain.get('certificate_arn'))
        else:
            certificate = acm.Certificate(
                self,
                'CustomDomainCertificate',
                domain_name=custom_domain['hosted_zone_name'],
                subject_alternative_names=[f'*.{custom_domain["hosted_zone_name"]}'],
                validation=acm.CertificateValidation.from_dns(hosted_zone=hosted_zone),
            )

        frontend_sg = ec2.SecurityGroup(
            self,
            'FargateTaskFrontendSG',
            security_group_name=f'{resource_prefix}-{envname}-albfront-service-sg',
            vpc=vpc,
            allow_all_outbound=True,
        )
        frontend_alb = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            f'FrontEndService{envname}',
            cluster=cluster,
            cpu=1024,
            memory_limit_mib=2048,
            service_name=f'frontend-{envname}',
            desired_count=2,
            certificate=certificate if (custom_domain and custom_domain.get('certificate_arn')) else None,
            domain_name=frontend_alternate_domain,
            domain_zone=hosted_zone,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                container_port=80,
                environment={
                    'AWS_REGION': self.region,
                    'envname': envname,
                    'LOGLEVEL': 'DEBUG',
                },
                task_role=task_role,
                image=ecs.ContainerImage.from_ecr_repository(
                    repository=ecr_repository, tag=frontend_image_tag
                ),
                enable_logging=True,
                log_driver=ecs.LogDriver.aws_logs(
                    stream_prefix='service',
                    log_group=self.create_log_group(
                        envname, resource_prefix, log_group_name='frontend'
                    ),
                ),
            ),
            public_load_balancer=False,
            assign_public_ip=False,
            open_listener=False,
            max_healthy_percent=100,
            min_healthy_percent=0,
            security_groups=[frontend_sg],
        )
        frontend_alb.target_group.configure_health_check(
            port='80',
            path='/',
            timeout=Duration.seconds(10),
            healthy_threshold_count=2,
            unhealthy_threshold_count=2,
            interval=Duration.seconds(15),
        )
        flb: elb.CfnLoadBalancer = frontend_alb.load_balancer.node.default_child
        flb.access_logging_policy = elb.CfnLoadBalancer.AccessLoggingPolicyProperty(
            enabled=True,
            s3_bucket_name=logs_bucket.bucket_name,
            s3_bucket_prefix='frontend',
        )
        self.allow_alb_access(frontend_alb, ip_ranges, vpc)

        userguide_sg = ec2.SecurityGroup(
            self,
            'FargateTaskUserGuideSG',
            security_group_name=f'{resource_prefix}-{envname}-userguide-service-sg',
            vpc=vpc,
            allow_all_outbound=True,
        )
        userguide_alb = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            f'UserGuideService{envname}',
            cluster=cluster,
            cpu=1024,
            memory_limit_mib=2048,
            service_name=f'userguide-{envname}',
            desired_count=1,
            certificate=certificate if (custom_domain and custom_domain.get('certificate_arn')) else None,
            domain_name=userguide_alternate_domain,
            domain_zone=hosted_zone,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                container_port=80,
                environment={
                    'AWS_REGION': self.region,
                    'envname': envname,
                    'LOGLEVEL': 'DEBUG',
                },
                task_role=task_role,
                image=ecs.ContainerImage.from_ecr_repository(
                    repository=ecr_repository, tag=userguide_image_tag
                ),
                enable_logging=True,
                log_driver=ecs.LogDriver.aws_logs(
                    stream_prefix='service',
                    log_group=self.create_log_group(
                        envname, resource_prefix, log_group_name='userguide'
                    ),
                ),
            ),
            public_load_balancer=False,
            assign_public_ip=False,
            open_listener=False,
            max_healthy_percent=100,
            min_healthy_percent=0,
            security_groups=[userguide_sg],
        )
        ulb: elb.CfnLoadBalancer = userguide_alb.load_balancer.node.default_child
        ulb.access_logging_policy = elb.CfnLoadBalancer.AccessLoggingPolicyProperty(
            enabled=True,
            s3_bucket_name=logs_bucket.bucket_name,
            s3_bucket_prefix='userguide',
        )
        userguide_alb.target_group.configure_health_check(
            port='80',
            path='/',
            timeout=Duration.seconds(10),
            healthy_threshold_count=2,
            unhealthy_threshold_count=2,
            interval=Duration.seconds(15),
        )
        self.allow_alb_access(userguide_alb, ip_ranges, vpc)

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
