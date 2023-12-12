import os

from aws_cdk import (
    custom_resources as cr,
    aws_cognito as cognito,
    aws_ssm as ssm,
    aws_iam as iam,
    aws_lambda as _lambda,
    CfnOutput,
    BundlingOptions,
    Duration,
    CustomResource,
)

from .pyNestedStack import pyNestedClass
from .solution_bundling import SolutionBundling


class IdpStack(pyNestedClass):
    def __init__(
        self,
        scope,
        id,
        envname='dev',
        resource_prefix='dataall',
        vpc=None,
        prod_sizing=False,
        internet_facing=True,
        tooling_account_id=None,
        enable_cw_rum=False,
        cognito_user_session_timeout_inmins=43200,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)
        self.user_pool = cognito.UserPool(
            self,
            f'UserPool-{envname}',
            user_pool_name=f'{resource_prefix}-{envname}-userpool',
            self_sign_up_enabled=False,
            sign_in_aliases=cognito.SignInAliases(username=True, email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_digits=True,
                require_uppercase=True,
                require_lowercase=True,
                require_symbols=True,
            ),
        )
        cfn_user_pool: cognito.CfnUserPool = self.user_pool.node.default_child
        cfn_user_pool.user_pool_add_ons = cognito.CfnUserPool.UserPoolAddOnsProperty(
            advanced_security_mode='ENFORCED'
        )
        self.domain = cognito.UserPoolDomain(
            self,
            f'UserPool{envname}',
            user_pool=self.user_pool,
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix=f"{resource_prefix.replace('-', '')}{envname}{self.region.replace('-', '')}{self.account}"
            ),
        )

        self.client = cognito.UserPoolClient(
            self,
            f'AppClient-{envname}',
            user_pool=self.user_pool,
            prevent_user_existence_errors=True,
            refresh_token_validity=Duration.minutes(cognito_user_session_timeout_inmins),
        )

        if enable_cw_rum:
            self.identity_pool = cognito.CfnIdentityPool(
                self,
                f'IdentityPool-{envname}',
                allow_unauthenticated_identities=True,
                identity_pool_name=f'{resource_prefix}-{envname}-identity-pool',
            )

            self.identity_pool_policy = iam.Policy(
                self,
                f'IdentityPoolPolicy{envname}',
                policy_name=f'{resource_prefix}-{envname}-cognito-identity-pool-policy',
                statements=[
                    iam.PolicyStatement(
                        actions=['rum:PutRumEvents'],
                        resources=[
                            f'arn:aws:rum:{self.region}:{self.account}:appmonitor/{resource_prefix}*'
                        ],
                    )
                ],
            )

            self.identity_pool_role = iam.Role(
                self,
                f'IdentityPoolRole{envname}',
                role_name=f'{resource_prefix}-{envname}-cognito-identity-pool-role',
                assumed_by=iam.FederatedPrincipal(
                    'cognito-identity.amazonaws.com',
                    conditions={
                        'StringEquals': {
                            'cognito-identity.amazonaws.com:aud': self.identity_pool.ref
                        },
                        'ForAnyValue:StringLike': {
                            'cognito-identity.amazonaws.com:amr': 'unauthenticated'
                        },
                    },
                    assume_role_action='sts:AssumeRoleWithWebIdentity',
                ),
            )
            self.identity_pool_policy.attach_to_role(self.identity_pool_role)

            cognito.CfnIdentityPoolRoleAttachment(
                self,
                f'IdentityPoolRoleAttachment{envname}',
                identity_pool_id=self.identity_pool.ref,
                roles={
                    'unauthenticated': self.identity_pool_role.role_arn,
                },
            )
            ssm.StringParameter(
                self,
                'IdentityPoolNameParameter',
                parameter_name=f'/dataall/{envname}/cognito/identitypool',
                string_value=self.identity_pool.ref,
            )

        pool = ssm.StringParameter(
            self,
            'UserPoolIdParameter',
            parameter_name=f'/dataall/{envname}/cognito/userpool',
            string_value=self.user_pool.user_pool_id,
        )

        pool_arn = ssm.StringParameter(
            self,
            'UserPoolArnParameter',
            parameter_name=f'/dataall/{envname}/cognito/userpoolarn',
            string_value=self.user_pool.user_pool_arn,
        )

        clientid = ssm.StringParameter(
            self,
            'UserPoolClientIdParameter',
            parameter_name=f'/dataall/{envname}/cognito/appclient',
            string_value=self.client.user_pool_client_id,
        )

        domain_name = ssm.StringParameter(
            self,
            'DomainNameParameter',
            parameter_name=f'/dataall/{envname}/cognito/domain',
            string_value=self.domain.domain_name,
        )

        ssm.StringParameter(
            self,
            'UserPoolRegion',
            parameter_name=f'/dataall/{envname}/cognito/region',
            string_value=self.region,
        )

        cross_account_frontend_config_role = iam.Role(
            self,
            f'{resource_prefix}-{envname}-frontend-config-role',
            role_name=f'{resource_prefix}-{envname}-frontend-config-role',
            assumed_by=iam.AccountPrincipal(tooling_account_id),
        )
        cross_account_frontend_config_role.add_to_policy(
            iam.PolicyStatement(
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
                    f'arn:aws:cognito-idp:{self.region}:{self.account}:userpool/{self.user_pool.user_pool_id}',
                    f'arn:aws:kms:{self.region}:{self.account}:key/*',
                    f'arn:aws:ssm:*:{self.account}:parameter/*{resource_prefix}*',
                    f'arn:aws:ssm:*:{self.account}:parameter/*dataall*',
                    f'arn:aws:secretsmanager:{self.region}:{self.account}:secret:*{resource_prefix}*',
                    f'arn:aws:secretsmanager:{self.region}:{self.account}:secret:*dataall*',
                    f'arn:aws:rum:{self.region}:{self.account}:appmonitor/*{resource_prefix}*',
                ],
            ),
        )
        ssm.StringParameter(
            self,
            'CognitoConfigRoleName',
            parameter_name=f'/dataall/{envname}/cognito/crossAccountRole',
            string_value=cross_account_frontend_config_role.role_name,
        )

        if internet_facing:
            role_inline_policy = iam.Policy(
                self,
                f'CognitoSyncCustomResource{envname}',
                policy_name=f'{resource_prefix}-{envname}-cognito-sync-policy',
                statements=[
                    iam.PolicyStatement(
                        actions=[
                            'ssm:GetParametersByPath',
                            'ssm:GetParameters',
                            'ssm:GetParameter',
                            'ssm:Put*',
                        ],
                        resources=[
                            f'arn:aws:ssm:*:{self.account}:parameter/*{resource_prefix}*',
                            f'arn:aws:ssm:*:{self.account}:parameter/*dataall*',
                        ],
                    )
                ],
            )

            cognito_sync_role = iam.Role(
                self,
                f'CognitoSyncRole{envname}',
                role_name=f'{resource_prefix}-{envname}-cognito-sync-role',
                inline_policies={
                    f'CognitoSyncInlinePolicy{envname}': role_inline_policy.document
                },
                assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
            )

            cognito_sync_role.add_managed_policy(
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    'service-role/AWSLambdaVPCAccessExecutionRole'
                )
            )

            cognito_assets = os.path.realpath(
                os.path.join(
                    os.path.dirname(__file__),
                    '..',
                    'custom_resources',
                    'sync_congito_params',
                )
            )
            cognito_sync_handler = _lambda.Function(
                self,
                f'CognitoParamsSyncHandler{envname}',
                function_name=f'{resource_prefix}-{envname}-cognito-sync-cr',
                role=cognito_sync_role,
                handler='index.on_event',
                code=_lambda.Code.from_asset(
                    path=cognito_assets,
                    bundling=BundlingOptions(
                        image=_lambda.Runtime.PYTHON_3_9.bundling_image,
                        local=SolutionBundling(source_path=cognito_assets),
                    ),
                ),
                memory_size=512 if prod_sizing else 256,
                description='dataall Custom resource to sync cognito params to us-east-1',
                timeout=Duration.seconds(5 * 60),
                environment={'envname': envname, 'LOG_LEVEL': 'DEBUG'},
                vpc=vpc,
                runtime=_lambda.Runtime.PYTHON_3_9,
            )

            sync_provider = cr.Provider(
                self, f'CognitoProvider{envname}', on_event_handler=cognito_sync_handler
            )

            sync_cr = CustomResource(
                self,
                f'CognitoSyncCR{envname}',
                service_token=sync_provider.service_token,
                resource_type='Custom::SchemaHandlerResource',
                properties={'envname': envname},
            )

            sync_cr.node.add_dependency(pool)
            sync_cr.node.add_dependency(clientid)
            sync_cr.node.add_dependency(domain_name)
            sync_cr.node.add_dependency(pool_arn)

        CfnOutput(
            self,
            'CognitoDomainName',
            export_name=f'CognitoDomainName{envname}',
            value=self.domain.domain_name,
        )
        CfnOutput(
            self,
            'CognitoUserPoolId',
            export_name=f'CognitoUserPoolId{envname}',
            value=self.user_pool.user_pool_id,
        )
        CfnOutput(
            self,
            'CognitoAppCliendId',
            export_name=f'CognitoAppCliendId{envname}',
            value=self.client.user_pool_client_id,
        )
