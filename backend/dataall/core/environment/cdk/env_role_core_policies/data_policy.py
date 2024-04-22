import logging
from typing import List

from aws_cdk import aws_iam as iam

from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup

logger = logging.getLogger()


class S3Policy:
    """
    Class including all permissions needed to work with AWS Lambda.
    It allows data.all users to:
    -
    """

    def __init__(
        self,
        stack,
        id,
        name,
        account,
        region,
        tag_key,
        tag_value,
        resource_prefix,
        environment: Environment,
        team: EnvironmentGroup,
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

    def generate_data_access_policy(self, session) -> iam.Policy:
        """
        Creates aws_iam.Policy based on team datasets
        """
        statements: List[iam.PolicyStatement] = self.get_statements(session)

        for extension in S3Policy.__subclasses__():
            statements.extend(extension.get_statements(self, session=session))

        policy: iam.Policy = iam.Policy(
            self.stack,
            self.id,
            policy_name=self.name,
            statements=statements,
        )
        logger.debug(f'Final generated policy {policy.document.to_json()}')

        return policy

    def get_statements(self, *args, **kwargs):
        statements = [
            iam.PolicyStatement(
                sid='ListAll',
                actions=[
                    's3:ListAllMyBuckets',
                    's3:ListAccessPoints',
                    's3:GetBucketLocation',
                    'kms:ListAliases',
                    'kms:ListKeys',
                ],
                resources=['*'],
                effect=iam.Effect.ALLOW,
            )
        ]

        return statements
