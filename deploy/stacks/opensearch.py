import os
import sys

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

BACKEND_UTILS_PATH = '/backend/dataall/base'
parent_dir = os.path.dirname(os.path.realpath(__file__))
backend_dir = parent_dir.rsplit('/', 2)[0] + BACKEND_UTILS_PATH
sys.path.insert(0, backend_dir)

# ruff: noqa: E402
from utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)

# ruff: noqa: E402
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
        log_retention_duration=None,
        **kwargs,
    ):
        super().__init__(scope, id)

        db_security_group = ec2.SecurityGroup(
            self,
            f'ElasticSearchSecurityGroup{envname}',
            security_group_name=f'{resource_prefix}-{envname}-elasticsearch-sg',
            vpc=vpc,
            allow_all_outbound=False,
            disable_inline_rules=True,
        )

        key = aws_kms.Key(
            self,
            'ESKMSKey',
            removal_policy=RemovalPolicy.DESTROY if not prod_sizing else RemovalPolicy.RETAIN,
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
            retention=getattr(logs.RetentionDays, log_retention_duration),
        )

        self.domain = opensearch.Domain(
            self,
            f'OpenSearchDomain{envname}',
            domain_name=self._set_os_compliant_name(prefix=f'{resource_prefix}-{envname}', name='domain'),
            version=opensearch.EngineVersion.OPENSEARCH_1_1,
            capacity=opensearch.CapacityConfig(data_nodes=2, master_nodes=3 if prod_sizing else 0),
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
                    subnets=vpc.select_subnets(subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT, one_per_az=True).subnets[:2]
                )
            ],
            security_groups=[db_security_group],
            encryption_at_rest=opensearch.EncryptionAtRestOptions(enabled=True, kms_key=key),
            access_policies=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=['es:*'],
                    resources=['*'],
                    principals=[iam.AnyPrincipal()],
                )
            ],
        )

        if lambdas:
            l: _lambda.Function
            for l in lambdas:
                self.domain.connections.allow_from(
                    l.connections,
                    ec2.Port.tcp(443),
                    f'Allow dataall opensearch to lambda {l.function_name}',
                )

        if ecs_security_groups:
            for sg in ecs_security_groups:
                sg_connection = ec2.Connections(security_groups=[sg])
                self.domain.connections.allow_from(
                    sg_connection,
                    ec2.Port.tcp(443),
                    'Allow dataall opensearch to ecs sg',
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

    @property
    def domain_name(self) -> str:
        return self.domain.domain_name

    @property
    def domain_endpoint(self) -> str:
        return self.domain.domain_endpoint

    @staticmethod
    def _set_os_compliant_name(prefix: str, name: str) -> str:
        compliant_name = NamingConventionService(
            target_uri=None,
            target_label=name,
            pattern=NamingConventionPattern.OPENSEARCH,
            resource_prefix=prefix,
        ).build_compliant_name()
        return compliant_name
