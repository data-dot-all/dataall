import json

from aws_cdk import (
    aws_kms as kms,
    aws_secretsmanager as sm,
    RemovalPolicy,
    Duration,
)

from .pyNestedStack import pyNestedClass


class SecretsManagerStack(pyNestedClass):
    def __init__(
        self,
        scope,
        id,
        envname='dev',
        resource_prefix='dataall',
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        self.canary_user = sm.Secret(
            self,
            f'canary-user',
            secret_name=f'{resource_prefix}-{envname}-cognito-canary-user',
            generate_secret_string=sm.SecretStringGenerator(
                secret_string_template=json.dumps({'username': f'cwcanary-{self.account}'}),
                generate_string_key='password',
                include_space=False,
                password_length=12,
            ),
            encryption_key=self.external_id_key,
            description=f'Stores dataall Cognito canary user',
            removal_policy=RemovalPolicy.DESTROY,
        )
        self.canary_user.add_rotation_schedule(
            id=envname[:2],
            automatically_after=Duration.days(90),
            hosted_rotation=sm.HostedRotation.postgre_sql_single_user(),
        )
