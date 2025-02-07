from typing import cast

from aws_cdk import (
    aws_ec2 as ec2,
    aws_ssm as ssm,
    aws_iam as iam,
    aws_logs as logs,
    CfnOutput,
    RemovalPolicy,
)

from .pyNestedStack import pyNestedClass


class VpcStack(pyNestedClass):
    def __init__(
        self,
        scope,
        id,
        envname='dev',
        vpc_id=None,
        vpc_endpoints_sg=None,
        cidr=None,
        resource_prefix=None,
        restricted_nacl=False,
        log_retention_duration=None,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)
        self.log_retention_duration = log_retention_duration

        if vpc_id:
            self.vpc = ec2.Vpc.from_lookup(self, 'vpc', vpc_id=vpc_id)
        else:
            self.create_new_vpc(cidr, envname, resource_prefix, restricted_nacl)

        if vpc_endpoints_sg:
            self.vpce_security_group = ec2.SecurityGroup.from_security_group_id(
                self, id='VpceSg', security_group_id=vpc_endpoints_sg, mutable=False
            )
        else:
            self.vpce_security_group = ec2.SecurityGroup(
                self,
                'vpc-sg',
                security_group_name=f'{resource_prefix}-{envname}-vpce-sg',
                vpc=cast(ec2.IVpc, self.vpc),
                allow_all_outbound=False,
                disable_inline_rules=True,
            )
            self._create_vpc_endpoints()

        self.private_subnets = []
        if self.vpc.private_subnets:
            for index, subnet in enumerate(self.vpc.private_subnets):
                self.private_subnets.append(subnet.subnet_id)
                CfnOutput(
                    self,
                    f'{resource_prefix}-{envname}-privateSubnet-{index + 1}',
                    export_name=f'{resource_prefix}-{envname}-privateSubnet-{index + 1}',
                    value=subnet.subnet_id,
                    description=f'{resource_prefix}-{envname}-privateSubnet-{index + 1}',
                )

        ssm.StringParameter(
            self,
            'VpcPrivateSubnets',
            parameter_name=f'/dataall/{envname}/vpc/private_subnets',
            string_value=(','.join(self.private_subnets)),
        )

        if self.vpc.public_subnets:
            self.public_subnets = [subnet.subnet_id for subnet in self.vpc.public_subnets]
            ssm.StringParameter(
                self,
                'VpcPublicSubnets',
                parameter_name=f'/dataall/{envname}/vpc/public_subnets',
                string_value=(','.join(self.public_subnets)),
            )

        ssm.StringParameter(
            self,
            'VpcIdParam',
            parameter_name=f'/dataall/{envname}/vpc/vpc_id',
            string_value=self.vpc.vpc_id,
        )

        CfnOutput(
            self,
            f'{resource_prefix}-{envname}-vpcId',
            export_name=f'{resource_prefix}-{envname}-vpcId',
            value=self.vpc.vpc_id,
            description=f'{resource_prefix}-{envname}-vpcId',
        )

        if self.vpc.public_subnets:
            CfnOutput(
                self,
                f'{resource_prefix}-{envname}-publicSubnets',
                export_name=f'{resource_prefix}-{envname}-publicSubnets',
                value=(','.join(self.public_subnets)),
                description=f'{resource_prefix}-{envname}-publicSubnets',
            )

        if self.vpc.vpc_cidr_block:
            CfnOutput(
                self,
                f'{resource_prefix}-{envname}-cidrBlock',
                export_name=f'{resource_prefix}-{envname}-cidrBlock',
                value=self.vpc.vpc_cidr_block,
                description=f'{resource_prefix}-{envname}-cidrBlock',
            )

    def create_new_vpc(self, cidr, envname, resource_prefix, restricted_nacl):
        self.vpc = ec2.Vpc(
            self,
            'VPC',
            max_azs=2,
            cidr=cidr or '172.31.0.0/16',
            subnet_configuration=[
                ec2.SubnetConfiguration(subnet_type=ec2.SubnetType.PUBLIC, name='Public', cidr_mask=20),
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT,
                    name='Private',
                    cidr_mask=24,
                ),
            ],
            nat_gateways=1,
        )

        if restricted_nacl:
            nacl = ec2.NetworkAcl(
                self,
                'RestrictedNACL',
                vpc=self.vpc,
                network_acl_name=f'{resource_prefix}-{envname}-restrictedNACL',
                subnet_selection=ec2.SubnetSelection(subnets=self.vpc.private_subnets + self.vpc.public_subnets),
            )
            nacl.add_entry(
                'entryOutbound',
                cidr=ec2.AclCidr.any_ipv4(),
                traffic=ec2.AclTraffic.all_traffic(),
                rule_number=100,
                direction=ec2.TrafficDirection.EGRESS,
                rule_action=ec2.Action.ALLOW,
            )
            nacl.add_entry(
                'entryInboundHTTPS',
                cidr=ec2.AclCidr.any_ipv4(),
                traffic=ec2.AclTraffic.tcp_port(443),
                rule_number=100,
                direction=ec2.TrafficDirection.INGRESS,
                rule_action=ec2.Action.ALLOW,
            )
            nacl.add_entry(
                'entryInboundHTTP',
                cidr=ec2.AclCidr.any_ipv4(),
                traffic=ec2.AclTraffic.tcp_port(80),
                rule_number=101,
                direction=ec2.TrafficDirection.INGRESS,
                rule_action=ec2.Action.ALLOW,
            )
            nacl.add_entry(
                'entryInboundCustomTCP',
                cidr=ec2.AclCidr.any_ipv4(),
                traffic=ec2.AclTraffic.tcp_port_range(start_port=1024, end_port=65535),
                rule_number=102,
                direction=ec2.TrafficDirection.INGRESS,
                rule_action=ec2.Action.ALLOW,
            )
            nacl.add_entry(
                'entryInboundAllInVPC',
                cidr=ec2.AclCidr.ipv4(self.vpc.vpc_cidr_block),
                traffic=ec2.AclTraffic.all_traffic(),
                rule_number=103,
                direction=ec2.TrafficDirection.INGRESS,
                rule_action=ec2.Action.ALLOW,
            )

        flowlog_log_group = logs.LogGroup(
            self,
            f'{resource_prefix}/{envname}/flowlogs',
            log_group_name=f'{resource_prefix}/{envname}/flowlogs',
            removal_policy=RemovalPolicy.DESTROY,
            retention=getattr(logs.RetentionDays, self.log_retention_duration),
        )
        iam_policy = iam.PolicyDocument(
            assign_sids=True,
            statements=[
                iam.PolicyStatement(
                    actions=[
                        'logs:CreateLogStream',
                        'logs:PutLogEvents',
                        'logs:DescribeLogGroups',
                        'logs:DescribeLogStreams',
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=[flowlog_log_group.log_group_arn],
                )
            ],
        )
        iam_role = iam.Role(
            self,
            f'{resource_prefix}-{envname}-flowlogs-role',
            assumed_by=iam.ServicePrincipal('vpc-flow-logs.amazonaws.com'),
            inline_policies={f'{resource_prefix}-{envname}-flowlogs-policy': iam_policy},
        )
        ec2.CfnFlowLog(
            self,
            f'{resource_prefix}-{envname}-flowlog',
            deliver_logs_permission_arn=iam_role.role_arn,
            log_destination_type='cloud-watch-logs',
            log_group_name=flowlog_log_group.log_group_name,
            traffic_type='ALL',
            resource_type='VPC',
            resource_id=self.vpc.vpc_id,
        )

    def _create_vpc_endpoints(self) -> None:
        vpc_gateway_endpoints = {
            's3': ec2.GatewayVpcEndpointAwsService.S3,
        }
        vpc_interface_endpoints = {
            'ecr_docker_endpoint': ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER,
            'ecr_endpoint': ec2.InterfaceVpcEndpointAwsService.ECR,
            'ec2_endpoint': ec2.InterfaceVpcEndpointAwsService.EC2,
            'ecs': ec2.InterfaceVpcEndpointAwsService.ECS,
            'ecs_agent': ec2.InterfaceVpcEndpointAwsService.ECS_AGENT,
            'ecs_telemetry': ec2.InterfaceVpcEndpointAwsService.ECS_TELEMETRY,
            'ssm_endpoint': ec2.InterfaceVpcEndpointAwsService.SSM,
            'ssm_messages_endpoint': ec2.InterfaceVpcEndpointAwsService.SSM_MESSAGES,
            'secrets_endpoint': ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
            'kms_endpoint': ec2.InterfaceVpcEndpointAwsService.KMS,
            'sqs': ec2.InterfaceVpcEndpointAwsService.SQS,
            'sns_endpoint': ec2.InterfaceVpcEndpointAwsService.SNS,
            'kinesis_endpoint': ec2.InterfaceVpcEndpointAwsService.KINESIS_STREAMS,
            'sts_endpoint': ec2.InterfaceVpcEndpointAwsService.STS,
            'autoscaling': ec2.InterfaceVpcEndpointAwsService('autoscaling'),
            'cloudformation_endpoint': ec2.InterfaceVpcEndpointAwsService.CLOUDFORMATION,
            'codebuild_endpoint': ec2.InterfaceVpcEndpointAwsService.CODEBUILD,
            'cloudwatch_logs_endpoint': ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
            'rds_endpoint': ec2.InterfaceVpcEndpointAwsService.RDS,
            'rds_data_endpoint': ec2.InterfaceVpcEndpointAwsService.RDS_DATA,
            'sagemaker_api': ec2.InterfaceVpcEndpointAwsService.SAGEMAKER_API,
            'glue': ec2.InterfaceVpcEndpointAwsService.GLUE,
            'lakeformation': ec2.InterfaceVpcEndpointAwsService.LAKE_FORMATION,
            'athena': ec2.InterfaceVpcEndpointAwsService.ATHENA,
            'codecommit': ec2.InterfaceVpcEndpointAwsService.CODECOMMIT,
            'git-codecommit': ec2.InterfaceVpcEndpointAwsService.CODECOMMIT_GIT,
        }

        for name, gateway_vpc_endpoint_service in vpc_gateway_endpoints.items():
            self.vpc.add_gateway_endpoint(
                id=name,
                service=gateway_vpc_endpoint_service,
                subnets=[
                    ec2.SubnetSelection(subnets=self.vpc.private_subnets),
                ],
            )

        for name, interface_service in vpc_interface_endpoints.items():
            self.vpc.add_interface_endpoint(
                id=name,
                service=interface_service,
                subnets=ec2.SubnetSelection(subnets=self.vpc.private_subnets),
                private_dns_enabled=True,
                security_groups=[cast(ec2.ISecurityGroup, self.vpce_security_group)],
            )
        self.vpc.add_interface_endpoint(
            id='code_artifact_repo_endpoint',
            service=cast(
                ec2.IInterfaceVpcEndpointService,
                ec2.InterfaceVpcEndpointAwsService('codeartifact.repositories'),
            ),
            subnets=ec2.SubnetSelection(subnets=self.vpc.private_subnets),
            private_dns_enabled=True,
            security_groups=[cast(ec2.ISecurityGroup, self.vpce_security_group)],
        )
        self.vpc.add_interface_endpoint(
            id='code_artifact_api_endpoint',
            service=cast(
                ec2.IInterfaceVpcEndpointService,
                ec2.InterfaceVpcEndpointAwsService('codeartifact.api'),
            ),
            subnets=ec2.SubnetSelection(subnets=self.vpc.private_subnets),
            private_dns_enabled=True,
            security_groups=[cast(ec2.ISecurityGroup, self.vpce_security_group)],
        )
