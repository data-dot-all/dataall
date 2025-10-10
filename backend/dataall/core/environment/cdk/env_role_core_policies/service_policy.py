import logging
from typing import List

from aws_cdk import aws_iam

from dataall.core.environment.db.environment_models import EnvironmentGroup, Environment

logger = logging.getLogger()


class ServicePolicy(object):
    """
    Generic Class to define AWS-services policies added to an IAM role
    """

    def __init__(
        self,
        stack,
        id,
        name,
        account,
        region,
        role_name,
        tag_key,
        tag_value,
        resource_prefix,
        environment: Environment,
        team: EnvironmentGroup,
        permissions,
    ):
        self.stack = stack
        self.id = id
        self.name = name
        self.account = account
        self.region = region
        self.tag_key = tag_key
        self.tag_value = tag_value
        self.resource_prefix = resource_prefix
        self.environment = environment
        self.team = team
        self.permissions = permissions
        self.role_name = role_name

    def generate_policies(self) -> [aws_iam.ManagedPolicy]:
        """
        Creates aws_iam.Policy based on declared subclasses of Policy object
        """
        policies: [aws_iam.ManagedPolicy] = [
            # This policy adds some minimum actions required independent from the services enabled for the group
            aws_iam.ManagedPolicy(
                self.stack,
                self.id,
                managed_policy_name=f'{self.id}-0',
                statements=[
                    aws_iam.PolicyStatement(
                        sid='ListActions',
                        effect=aws_iam.Effect.ALLOW,
                        actions=[
                            'ec2:Describe*',
                            'logs:Describe*',
                            'logs:Get*',
                            'logs:List*',
                            'cloudwatch:GetMetricData',
                            'events:ListRuleNamesByTarget',
                            'iam:list*',
                            'iam:Get*',
                            'tag:GetResources',
                            'tag:GetTagValues',
                            'tag:GetTagKeys',
                        ],
                        resources=['*'],
                    ),
                    aws_iam.PolicyStatement(
                        sid='IAMCreatePolicy',
                        effect=aws_iam.Effect.ALLOW,
                        actions=[
                            'iam:CreatePolicy',
                            'iam:CreateServiceLinkedRole',
                        ],
                        resources=[
                            f'arn:aws:iam::{self.account}:policy/{self.resource_prefix}*',
                            f'arn:aws:iam::{self.account}:role/aws-service-role/*',
                        ],
                    ),
                    aws_iam.PolicyStatement(
                        sid='CreateServiceRole',
                        actions=[
                            'iam:CreateRole',
                        ],
                        resources=[f'arn:aws:iam::{self.account}:role/service-role/*'],
                    ),
                    aws_iam.PolicyStatement(
                        sid='PassRole',
                        actions=[
                            'iam:PassRole',
                        ],
                        resources=[f'arn:aws:iam::{self.account}:role/{self.role_name}'],
                        conditions={
                            'StringEquals': {
                                'iam:PassedToService': [
                                    'glue.amazonaws.com',
                                    'omics.amazonaws.com',
                                    'lambda.amazonaws.com',
                                    'sagemaker.amazonaws.com',
                                    'states.amazonaws.com',
                                    'sagemaker.amazonaws.com',
                                    'databrew.amazonaws.com',
                                    'codebuild.amazonaws.com',
                                    'codepipeline.amazonaws.com',
                                ]
                            }
                        },
                    ),
                ],
            )
        ]

        services = ServicePolicy.__subclasses__()

        statements = []
        for service in services:
            statements.extend(service.get_statements(self, self.permissions))

        statements_chunks: list = [statements[i : i + 10] for i in range(0, len(statements), 10)]

        for index, chunk in enumerate(statements_chunks):
            policies.append(
                aws_iam.ManagedPolicy(
                    self.stack,
                    f'{self.id}-{index + 1}',
                    managed_policy_name=f'{self.id}-{index + 1}',
                    statements=chunk,
                )
            )
        return policies

    def get_statements(self, group_permissions, **kwargs) -> List[aws_iam.PolicyStatement]:
        """
        This method implements a policy based on a tag key and optionally a resource prefix
        :return: list
        """
        raise NotImplementedError('Policy subclasses need to implement the get_statements class method')
