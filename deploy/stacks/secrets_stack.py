import json

from aws_cdk import Duration, RemovalPolicy
from aws_cdk import aws_kms as kms
from aws_cdk import aws_secretsmanager as sm

from .pyNestedStack import pyNestedClass


class SecretsManagerStack(pyNestedClass):
    def __init__(
        self,
        scope,
        id,
        envname="dev",
        resource_prefix="dataall",
        enable_cw_canaries=False,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        self.external_id_key = kms.Key(
            self,
            f"ExternalIdSecretKey{envname}",
            alias=f"{resource_prefix}-{envname}-externalId-key",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.DESTROY,
        )

        self.external_id_secret = sm.Secret(
            self,
            f"ExternalIdSecret{envname}",
            secret_name=f"dataall-externalId-{envname}",
            generate_secret_string=sm.SecretStringGenerator(exclude_punctuation=True),
            encryption_key=self.external_id_key,
            description=f"Stores dataall external id for environment {envname}",
            removal_policy=RemovalPolicy.DESTROY,
        )

        self.pivot_role_name_key = kms.Key(
            self,
            f"PivotRoleNameSecretKey{envname}",
            alias=f"{resource_prefix}-{envname}-pivotrolename-key",
            enable_key_rotation=True,
        )

        self.pivot_role_name_secret = sm.CfnSecret(
            self,
            f"PivotRoleNameSecret{envname}",
            name=f"dataall-pivot-role-name-{envname}",
            secret_string="dataallPivotRole",
            kms_key_id=self.pivot_role_name_key.key_id,
            description=f"Stores dataall pivot role name for environment {envname}",
        )

        self.cognito_default_user = kms.Key(
            self,
            f"{resource_prefix}-{envname}-cognito-defaultuser-key",
            alias=f"{resource_prefix}-{envname}-cognito-defaultuser-key",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.DESTROY,
        )

        if enable_cw_canaries:
            self.canary_user = sm.Secret(
                self,
                f"canary-user",
                secret_name=f"{resource_prefix}-{envname}-cognito-canary-user",
                generate_secret_string=sm.SecretStringGenerator(
                    secret_string_template=json.dumps({"username": f"cwcanary-{self.account}"}),
                    generate_string_key="password",
                    include_space=False,
                    password_length=12,
                ),
                encryption_key=self.external_id_key,
                description=f"Stores dataall Cognito canary user",
                removal_policy=RemovalPolicy.DESTROY,
            )
            self.canary_user.add_rotation_schedule(
                id=envname[:2],
                automatically_after=Duration.days(90),
                hosted_rotation=sm.HostedRotation.postgre_sql_single_user(),
            )
