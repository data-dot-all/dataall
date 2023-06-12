import logging
from typing import List

from aws_cdk import aws_iam

from ....db import permissions
from ....db import models

logger = logging.getLogger()


class ServicePolicy(object):
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
        environment: models.Environment,
        team: models.EnvironmentGroup,
        permissions,
    ):
        self.stack = stack
        self.id = id
        self.name = name
        self.account = account
        self.region = region
        self.environment = environment
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
        from ._lambda import Lambda
        from .athena import Athena
        from .cloudformation import Cloudformation
        from .aws_cicd import AwsCICD
        from .databrew import Databrew
        from .glue import Glue, GlueCatalog
        from .quicksight import QuickSight
        from .sagemaker import Sagemaker
        from .secretsmanager import SecretsManager
        from .ssm import SSM
        from .stepfunctions import StepFunctions



        policies: [aws_iam.ManagedPolicy] = [
            # This policy covers the minumum actions required independent
            # of the service permissions given to the group.
            aws_iam.ManagedPolicy(
                self.stack,
                self.id,
                managed_policy_name=f'{self.id}-0',
                statements=[
                    aws_iam.PolicyStatement(
                        sid="ListActions",
                        effect=aws_iam.Effect.ALLOW,
                        actions=[
                            'ec2:Describe*',
                            'logs:Describe*',
                            'logs:Get*',
                            'logs:List*',
                            'iam:list*',
                            'iam:Get*',
                            'iam:CreateServiceLinkedRole',
                            'tag:GetResources',
                            'tag:GetTagValues',
                            'tag:GetTagKeys',
                        ],
                        resources=['*'],
                    ),
                    aws_iam.PolicyStatement(
                        sid="PassRole",
                        actions=[
                            'iam:PassRole',
                        ],
                        resources=[
                            f'arn:aws:iam::{self.account}:role/{self.role_name}'
                        ],
                        conditions={
                            "StringEquals": {
                                "iam:PassedToService": [
                                    "glue.amazonaws.com",
                                    "lambda.amazonaws.com",
                                    "sagemaker.amazonaws.com"
                                ]
                            }
                        }
                    ),
                ],
            )
        ]

        services = ServicePolicy.__subclasses__()

        if permissions.CREATE_DATASET not in self.permissions:
            services.remove(Databrew)
            services.remove(Glue)
        if (
            permissions.CREATE_NOTEBOOK not in self.permissions
            and permissions.CREATE_SGMSTUDIO_NOTEBOOK not in self.permissions
        ):
            services.remove(Sagemaker)
        if permissions.CREATE_PIPELINE not in self.permissions:
            services.remove(Lambda)
            services.remove(AwsCICD)
            services.remove(StepFunctions)
        if permissions.CREATE_DASHBOARD not in self.permissions:
            services.remove(QuickSight)

        statements = []
        for service in services:
            statements.extend(service.get_statements(self))

        statements_chunks: list = [
            statements[i : i + 8] for i in range(0, len(statements), 8)
        ]

        for index, chunk in enumerate(statements_chunks):
            policies.append(
                aws_iam.ManagedPolicy(
                    self.stack,
                    f'{self.id}-{index+1}',
                    managed_policy_name=f'{self.id}-{index+1}',
                    statements=chunk,
                )
            )
        return policies

    def get_statements(self, **kwargs) -> List[aws_iam.PolicyStatement]:
        """
        This method implements a policy based on a tag key and optionally a resource prefix
        :return: list
        """
        raise NotImplementedError(
            'Policy subclasses need to implement the get_statements class method'
        )
