import json
import os
import sys

from typing import Any, Dict, List, Optional
from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_ssm as ssm,
    aws_opensearchserverless as opensearchserverless,
    aws_kms,
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


class OpenSearchServerlessStack(pyNestedClass):
    def __init__(
        self,
        scope,
        id,
        envname='dev',
        resource_prefix='dataall',
        vpc: ec2.Vpc = None,
        vpc_endpoints_sg: ec2.SecurityGroup = None,
        lambdas: Optional[List[_lambda.Function]] = None,
        ecs_task_role: Optional[iam.Role] = None,
        prod_sizing=False,
        **kwargs,
    ):
        super().__init__(scope, id)

        self.cfn_collection = opensearchserverless.CfnCollection(
            self,
            f'OpenSearchCollection{envname}',
            name=self._set_os_compliant_name(prefix=f'{resource_prefix}-{envname}', name='collection'),
            type='SEARCH',
        )

        key = aws_kms.Key(
            self,
            'AOSSKMSKey',
            removal_policy=RemovalPolicy.DESTROY if not prod_sizing else RemovalPolicy.RETAIN,
            alias=f'{resource_prefix}-{envname}-opensearch-serverless',
            enable_key_rotation=True,
        )

        cfn_encryption_policy = opensearchserverless.CfnSecurityPolicy(
            self,
            f'OpenSearchCollectionEncryptionPolicy{envname}',
            name=self._set_os_compliant_name(prefix=f'{resource_prefix}-{envname}', name='encryption-policy'),
            type='encryption',
            policy=self._get_encryption_policy(
                collection_name=self.cfn_collection.name,
                kms_key_arn=key.key_arn,
            ),
        )

        cfn_vpc_endpoint = (
            opensearchserverless.CfnVpcEndpoint(
                self,
                f'OpenSearchCollectionVpcEndpoint{envname}',
                name=self._set_os_compliant_name(prefix=f'{resource_prefix}-{envname}', name='vpc-endpoint'),
                vpc_id=vpc.vpc_id,
                security_group_ids=[vpc_endpoints_sg.security_group_id],
                subnet_ids=[subnet.subnet_id for subnet in vpc.private_subnets],
            )
            if vpc and vpc_endpoints_sg
            else None
        )

        cfn_network_policy = opensearchserverless.CfnSecurityPolicy(
            self,
            f'OpenSearchCollectionNetworkPolicy{envname}',
            name=self._set_os_compliant_name(prefix=f'{resource_prefix}-{envname}', name='network-policy'),
            type='network',
            policy=self._get_network_policy(
                collection_name=self.cfn_collection.name,
                vpc_endpoints=[cfn_vpc_endpoint.attr_id] if vpc else None,
            ),
        )

        self.cfn_collection.add_depends_on(cfn_encryption_policy)
        self.cfn_collection.add_depends_on(cfn_network_policy)

        principal_arns: List[str] = [fn.role.role_arn for fn in lambdas] if lambdas else []
        if ecs_task_role:
            principal_arns.append(ecs_task_role.role_arn)

        opensearchserverless.CfnAccessPolicy(
            self,
            f'OpenSearchCollectionAccessPolicy{envname}',
            name=self._set_os_compliant_name(prefix=f'{resource_prefix}-{envname}', name='access-policy'),
            type='data',
            policy=self._get_access_policy(
                collection_name=self.cfn_collection.name,
                principal_arns=principal_arns,
            ),
        )

        ssm.StringParameter(
            self,
            'ElasticSearchEndpointParameter',
            parameter_name=f'/dataall/{envname}/elasticsearch/endpoint',
            string_value=f'{self.cfn_collection.attr_id}.{self.region}.aoss.amazonaws.com',
        )

        ssm.StringParameter(
            self,
            'ElasticSearchDomainParameter',
            parameter_name=f'/dataall/{envname}/elasticsearch/domain',
            string_value=self.cfn_collection.name,
        )

        ssm.StringParameter(
            self,
            'ElasticSearchServiceParameter',
            parameter_name=f'/dataall/{envname}/elasticsearch/service',
            string_value='aoss',
        )

    @property
    def collection_id(self) -> str:
        return self.cfn_collection.attr_id

    @property
    def collection_name(self) -> str:
        return self.cfn_collection.name

    @staticmethod
    def _get_encryption_policy(collection_name: str, kms_key_arn: Optional[str] = None) -> str:
        policy: Dict[str, Any] = {
            'Rules': [
                {
                    'ResourceType': 'collection',
                    'Resource': [
                        f'collection/{collection_name}',
                    ],
                }
            ],
        }
        if kms_key_arn:
            policy['KmsARN'] = kms_key_arn
        else:
            policy['AWSOwnedKey'] = True
        return json.dumps(policy)

    @staticmethod
    def _get_network_policy(collection_name: str, vpc_endpoints: Optional[List[str]] = None) -> str:
        policy: List[Dict[str, Any]] = [
            {
                'Rules': [
                    {
                        'ResourceType': 'dashboard',
                        'Resource': [
                            f'collection/{collection_name}',
                        ],
                    },
                    {
                        'ResourceType': 'collection',
                        'Resource': [
                            f'collection/{collection_name}',
                        ],
                    },
                ],
            }
        ]
        if vpc_endpoints:
            policy[0]['SourceVPCEs'] = vpc_endpoints
        else:
            policy[0]['AllowFromPublic'] = True
        return json.dumps(policy)

    @staticmethod
    def _get_access_policy(collection_name: str, principal_arns: List[str]) -> str:
        policy = [
            {
                'Rules': [
                    {
                        'ResourceType': 'index',
                        'Resource': [
                            f'index/{collection_name}/*',
                        ],
                        'Permission': [
                            'aoss:*',
                        ],
                    },
                    {
                        'ResourceType': 'collection',
                        'Resource': [
                            f'collection/{collection_name}',
                        ],
                        'Permission': [
                            'aoss:*',
                        ],
                    },
                ],
                'Principal': principal_arns,
            }
        ]
        return json.dumps(policy)

    @staticmethod
    def _set_os_compliant_name(prefix: str, name: str) -> str:
        compliant_name = NamingConventionService(
            target_uri=None,
            target_label=name,
            pattern=NamingConventionPattern.OPENSEARCH_SERVERLESS,
            resource_prefix=prefix,
        ).build_compliant_name()
        return compliant_name
