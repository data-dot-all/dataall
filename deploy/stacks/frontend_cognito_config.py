from datetime import datetime

from aws_cdk import (
    aws_lambda as _lambda,
    aws_iam as iam,
    Duration,
    RemovalPolicy,
    aws_kms,
)
from aws_cdk.triggers import TriggerFunction

from custom_resources.utils import get_lambda_code
from .pyNestedStack import pyNestedClass


class FrontendCognitoConfig(pyNestedClass):
    def __init__(
        self,
        scope,
        id,
        envname='dev',
        resource_prefix='dataall',
        custom_domain=None,
        backend_region=None,
        execute_after=[],
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        lambda_env_key = aws_kms.Key(
            self,
            f'{resource_prefix}-{envname}-cogn-url-lambda-env-var-key',
            removal_policy=RemovalPolicy.DESTROY,
            alias=f'{resource_prefix}-{envname}-cogn-url-lambda-env-var-key',
            enable_key_rotation=True,
            policy=iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        resources=['*'],
                        effect=iam.Effect.ALLOW,
                        principals=[
                            iam.AccountPrincipal(account_id=self.account),
                        ],
                        actions=['kms:*'],
                    ),
                    iam.PolicyStatement(
                        resources=['*'],
                        effect=iam.Effect.ALLOW,
                        principals=[
                            iam.ServicePrincipal(service='lambda.amazonaws.com'),
                        ],
                        actions=['kms:GenerateDataKey*', 'kms:Decrypt'],
                    ),
                ],
            ),
        )

        cognito_config_code = get_lambda_code('cognito_config')

        TriggerFunction(
            self,
            'TriggerFunction-CognitoUrlsConfig',
            function_name=f'{resource_prefix}-{envname}-cognito-urls',
            description='dataall CognitoUrlsConfig trigger function',
            initial_policy=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        'secretsmanager:DescribeSecret',
                        'secretsmanager:GetSecretValue',
                        'ssm:GetParameterHistory',
                        'ssm:GetParameters',
                        'ssm:GetParameter',
                        'ssm:GetParametersByPath',
                        'kms:Decrypt',
                        'kms:GenerateDataKey',
                        'kms:DescribeKey',
                        'rum:GetAppMonitor',
                    ],
                    resources=[
                        f'arn:aws:kms:{self.region}:{self.account}:key/*',
                        f'arn:aws:ssm:*:{self.account}:parameter/*dataall*',
                        f'arn:aws:secretsmanager:{self.region}:{self.account}:secret:*dataall*',
                        f'arn:aws:rum:{self.region}:{self.account}:appmonitor/*dataall*',
                    ],
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        'cognito-idp:AddCustomAttributes',
                        'cognito-idp:UpdateUserPool',
                        'cognito-idp:DescribeUserPoolClient',
                        'cognito-idp:CreateGroup',
                        'cognito-idp:UpdateUserPoolClient',
                        'cognito-idp:AdminSetUserPassword',
                        'cognito-idp:AdminCreateUser',
                        'cognito-idp:DescribeUserPool',
                        'cognito-idp:AdminAddUserToGroup',
                    ],
                    resources=[f'arn:aws:cognito-idp:{backend_region}:{self.account}:userpool/*'],
                ),
            ],
            code=cognito_config_code,
            memory_size=256,
            timeout=Duration.minutes(15),
            environment={
                'envname': envname,
                'deployment_region': backend_region,
                'custom_domain': str(bool(custom_domain)),
                'timestamp': datetime.utcnow().isoformat(),
            },
            environment_encryption=lambda_env_key,
            tracing=_lambda.Tracing.ACTIVE,
            retry_attempts=0,
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler='cognito_urls.handler',
            execute_after=execute_after,
            execute_on_handler_change=True,
            logging_format=_lambda.LoggingFormat.JSON,
        )
