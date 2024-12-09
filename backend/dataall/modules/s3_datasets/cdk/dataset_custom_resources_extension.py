import os
import logging
import pathlib
from aws_cdk import (
    custom_resources as cr,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_destinations as lambda_destination,
    aws_ssm as ssm,
    aws_sqs as sqs,
    aws_kms as kms,
    RemovalPolicy,
    Duration,
    CustomResource,
)

from dataall.core.environment.cdk.environment_stack import EnvironmentSetup, EnvironmentStackExtension

log = logging.getLogger(__name__)


class DatasetCustomResourcesExtension(EnvironmentStackExtension):
    """Extends an environment stack for LakeFormation settings custom resource and Glue database custom resource"""

    @staticmethod
    def extent(setup: EnvironmentSetup):
        _environment = setup.environment()
        kms_key = DatasetCustomResourcesExtension.set_cr_kms_key(
            setup=setup, environment=_environment, group_roles=setup.group_roles, default_role=setup.default_role
        )

        lambda_env_key = kms.Key(
            setup,
            f'{_environment.resourcePrefix}-ds-cst-lambda-env-var-key',
            removal_policy=RemovalPolicy.DESTROY,
            alias=f'{_environment.resourcePrefix}-ds-cst-lambda-env-var-key',
            enable_key_rotation=True,
            policy=iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        resources=['*'],
                        effect=iam.Effect.ALLOW,
                        principals=[
                            iam.AccountPrincipal(account_id=_environment.AwsAccountId),
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

        # Lakeformation default settings custom resource
        # Set PivotRole as Lake Formation data lake admin
        entry_point = str(
            pathlib.PosixPath(os.path.dirname(__file__), './assets/lakeformationdefaultsettings').resolve()
        )

        lakeformation_cr_dlq = DatasetCustomResourcesExtension.set_dlq(
            setup=setup, queue_name=f'{_environment.resourcePrefix}-lfcr-{_environment.environmentUri}', kms_key=kms_key
        )
        lf_default_settings_custom_resource = _lambda.Function(
            setup,
            'LakeformationDefaultSettingsHandler',
            function_name=f'{_environment.resourcePrefix}-lf-settings-handler-{_environment.environmentUri}',
            role=setup.pivot_role,
            handler='index.on_event',
            code=_lambda.Code.from_asset(entry_point),
            memory_size=1664,
            description='This Lambda function is a cloudformation custom resource provider for Lakeformation default settings',
            timeout=Duration.seconds(5 * 60),
            environment={
                'envname': _environment.name,
                'LOG_LEVEL': 'DEBUG',
                'AWS_ACCOUNT': _environment.AwsAccountId,
                'DEFAULT_ENV_ROLE_ARN': _environment.EnvironmentDefaultIAMRoleArn,
                'DEFAULT_CDK_ROLE_ARN': _environment.CDKRoleArn,
            },
            environment_encryption=lambda_env_key,
            dead_letter_queue_enabled=True,
            dead_letter_queue=lakeformation_cr_dlq,
            on_failure=lambda_destination.SqsDestination(lakeformation_cr_dlq),
            runtime=_lambda.Runtime.PYTHON_3_9,
        )
        LakeformationDefaultSettingsProvider = cr.Provider(
            setup,
            f'{_environment.resourcePrefix}LakeformationDefaultSettingsProvider',
            on_event_handler=lf_default_settings_custom_resource,
            provider_function_env_encryption=lambda_env_key,
        )

        default_lf_settings = CustomResource(
            setup,
            f'{_environment.resourcePrefix}DefaultLakeFormationSettings',
            service_token=LakeformationDefaultSettingsProvider.service_token,
            resource_type='Custom::LakeformationDefaultSettings',
            properties={
                'DataLakeAdmins': [
                    f'arn:aws:iam::{_environment.AwsAccountId}:role/{setup.pivot_role_name}',
                ],
                'Version': 'data.all V2',
            },
        )

        ssm.StringParameter(
            setup,
            'LakeformationDefaultSettingsCustomeResourceFunctionArn',
            string_value=lf_default_settings_custom_resource.function_arn,
            parameter_name=f'/{_environment.resourcePrefix}/{_environment.environmentUri}/cfn/lf/defaultsettings/lambda/arn',
        )

        ssm.StringParameter(
            setup,
            'LakeformationDefaultSettingsCustomeResourceFunctionName',
            string_value=lf_default_settings_custom_resource.function_name,
            parameter_name=f'/{_environment.resourcePrefix}/{_environment.environmentUri}/cfn/lf/defaultsettings/lambda/name',
        )
        # Glue database custom resource
        # This Lambda is triggered with the creation of each dataset, it is not executed when the environment is created
        entry_point = str(pathlib.PosixPath(os.path.dirname(__file__), './assets/gluedatabasecustomresource').resolve())

        gluedb_lf_cr_dlq = DatasetCustomResourcesExtension.set_dlq(
            setup=setup,
            queue_name=f'{_environment.resourcePrefix}-gluedb-lf-cr-{_environment.environmentUri}',
            kms_key=kms_key,
        )
        gluedb_lf_custom_resource = _lambda.Function(
            setup,
            'GlueDatabaseLFCustomResourceHandler',
            function_name=f'{_environment.resourcePrefix}-gluedb-lf-handler-{_environment.environmentUri}',
            role=setup.pivot_role,
            handler='index.on_event',
            code=_lambda.Code.from_asset(entry_point),
            memory_size=1664,
            description='This Lambda function is a cloudformation custom resource provider for Glue database '
            'as Cfn currently does not support the CreateTableDefaultPermissions parameter',
            timeout=Duration.seconds(5 * 60),
            environment={
                'envname': _environment.name,
                'LOG_LEVEL': 'DEBUG',
                'AWS_ACCOUNT': _environment.AwsAccountId,
                'DEFAULT_ENV_ROLE_ARN': _environment.EnvironmentDefaultIAMRoleArn,
                'DEFAULT_CDK_ROLE_ARN': _environment.CDKRoleArn,
            },
            environment_encryption=lambda_env_key,
            dead_letter_queue_enabled=True,
            dead_letter_queue=gluedb_lf_cr_dlq,
            on_failure=lambda_destination.SqsDestination(gluedb_lf_cr_dlq),
            tracing=_lambda.Tracing.ACTIVE,
            runtime=_lambda.Runtime.PYTHON_3_9,
        )

        glue_db_provider = cr.Provider(
            setup,
            f'{_environment.resourcePrefix}GlueDbCustomResourceProvider',
            on_event_handler=gluedb_lf_custom_resource,
            provider_function_env_encryption=lambda_env_key,
        )
        ssm.StringParameter(
            setup,
            'GlueLFCustomResourceFunctionArn',
            string_value=gluedb_lf_custom_resource.function_arn,
            parameter_name=f'/{_environment.resourcePrefix}/{_environment.environmentUri}/cfn/custom-resources/gluehandler/lambda/arn',
        )

        ssm.StringParameter(
            setup,
            'GlueLFCustomResourceFunctionName',
            string_value=gluedb_lf_custom_resource.function_name,
            parameter_name=f'/{_environment.resourcePrefix}/{_environment.environmentUri}/cfn/custom-resources/gluehandler/lambda/name',
        )

        ssm.StringParameter(
            setup,
            'GlueLFCustomResourceProviderServiceToken',
            string_value=glue_db_provider.service_token,
            parameter_name=f'/{_environment.resourcePrefix}/{_environment.environmentUri}/cfn/custom-resources/gluehandler/provider/servicetoken',
        )

    @staticmethod
    def set_cr_kms_key(setup, environment, group_roles, default_role) -> kms.Key:
        key_policy = iam.PolicyDocument(
            assign_sids=True,
            statements=[
                iam.PolicyStatement(
                    actions=[
                        'kms:Encrypt',
                        'kms:Decrypt',
                        'kms:ReEncrypt*',
                        'kms:GenerateDataKey*',
                    ],
                    effect=iam.Effect.ALLOW,
                    principals=[
                        default_role,
                    ]
                    + group_roles,
                    resources=['*'],
                    conditions={'StringEquals': {'kms:ViaService': f'sqs.{environment.region}.amazonaws.com'}},
                ),
                iam.PolicyStatement(
                    actions=[
                        'kms:DescribeKey',
                        'kms:List*',
                        'kms:GetKeyPolicy',
                    ],
                    effect=iam.Effect.ALLOW,
                    principals=[
                        default_role,
                    ]
                    + group_roles,
                    resources=['*'],
                ),
            ],
        )

        kms_key = kms.Key(
            setup,
            f'dataall-environment-{environment.environmentUri}-cr-key',
            removal_policy=RemovalPolicy.DESTROY,
            alias=f'dataall-environment-{environment.environmentUri}-cr-key',
            enable_key_rotation=True,
            admins=[
                iam.ArnPrincipal(environment.CDKRoleArn),
            ],
            policy=key_policy,
        )
        return kms_key

    @staticmethod
    def set_dlq(setup, queue_name, kms_key) -> sqs.Queue:
        dlq = sqs.Queue(
            setup,
            f'{queue_name}-queue',
            queue_name=f'{queue_name}',
            retention_period=Duration.days(14),
            encryption=sqs.QueueEncryption.KMS,
            encryption_master_key=kms_key,
            data_key_reuse=Duration.days(1),
            removal_policy=RemovalPolicy.DESTROY,
        )

        enforce_tls_statement = iam.PolicyStatement(
            sid='Enforce TLS for all principals',
            effect=iam.Effect.DENY,
            principals=[
                iam.AnyPrincipal(),
            ],
            actions=[
                'sqs:*',
            ],
            resources=[dlq.queue_arn],
            conditions={
                'Bool': {'aws:SecureTransport': 'false'},
            },
        )

        dlq.add_to_resource_policy(enforce_tls_statement)
        return dlq
