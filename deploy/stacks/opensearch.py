from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_ssm as ssm,
    aws_opensearchservice as opensearch,
    aws_kms,
    aws_logs as logs,
    RemovalPolicy,
)

from .pyNestedStack import pyNestedClass


class OpenSearchStack(pyNestedClass):
    def __init__(
        self,
        scope,
        id,
        envname='dev',
        resource_prefix='dataall',
        vpc: ec2.Vpc = None,
        lambdas=None,
        ecs_security_groups: [ec2.SecurityGroup] = None,
        prod_sizing=False,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        db_security_group = ec2.SecurityGroup(
            self,
            f'ElasticSearchSecurityGroup{envname}',
            security_group_name=f'{resource_prefix}-{envname}-elasticsearch-sg',
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
                        connection=ec2.Port.tcp(443),
                        description=f'Allow dataall lambda {l.function_name}',
                    )

        if ecs_security_groups:
            for sg in ecs_security_groups:
                db_security_group.add_ingress_rule(
                    peer=sg,
                    connection=ec2.Port.tcp(443),
                    description=f'Allow dataall ECS cluster tasks',
                )

        key = aws_kms.Key(
            self,
            f'ESKMSKey',
            removal_policy=RemovalPolicy.DESTROY
            if not prod_sizing
            else RemovalPolicy.RETAIN,
            alias=f'{resource_prefix}-{envname}-elasticsearch',
            enable_key_rotation=True,
        )
        iam.CfnServiceLinkedRole(
            self, 'ServiceLinkedForElasticSearch', aws_service_name='opensearchservice.amazonaws.com'
        )

        es_app_log_group = logs.LogGroup(
            scope=self,
            id='EsAppLogGroup',
            log_group_name=f'/{resource_prefix}/{envname}/opensearch',
            removal_policy=RemovalPolicy.DESTROY,
        )

        self.domain = opensearch.Domain(
            self,
            f'OpenSearchDomain{envname}',
            domain_name=f'{resource_prefix}-{envname}-domain',
            version=opensearch.EngineVersion.OPENSEARCH_1_1,
            capacity=opensearch.CapacityConfig(
                data_nodes=2, master_nodes=3 if prod_sizing else 0
            ),
            enforce_https=True,
            ebs=opensearch.EbsOptions(volume_size=30 if prod_sizing else 20),
            enable_version_upgrade=True,
            node_to_node_encryption=True,
            logging=opensearch.LoggingOptions(
                app_log_enabled=True,
                app_log_group=es_app_log_group,
                slow_index_log_enabled=True,
                slow_search_log_enabled=True,
            ),
            vpc=vpc,
            zone_awareness=opensearch.ZoneAwarenessConfig(enabled=True),
            vpc_subnets=[
                ec2.SubnetSelection(
                    subnets=vpc.select_subnets(
                        subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT, one_per_az=True
                    ).subnets[:2]
                )
            ],
            security_groups=[db_security_group],
            encryption_at_rest=opensearch.EncryptionAtRestOptions(
                enabled=True, kms_key=key
            ),
            access_policies=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=['es:*'],
                    resources=['*'],
                    principals=[iam.AnyPrincipal()],
                )
            ],
        )

        ssm.StringParameter(
            self,
            'ElasticSearchEndpointParameter',
            parameter_name=f'/dataall/{envname}/elasticsearch/endpoint',
            string_value=str(self.domain.domain_endpoint),
        )

        ssm.StringParameter(
            self,
            'ElasticSearchDomainParameter',
            parameter_name=f'/dataall/{envname}/elasticsearch/domain',
            string_value=str(self.domain.domain_name),
        )

        ssm.StringParameter(
            self,
            'ElasticSearchSGParameter',
            parameter_name=f'/dataall/{envname}/elasticsearch/security_group_id',
            string_value=db_security_group.security_group_id,
        )
