import logging
import os
import pathlib
import shutil

from aws_cdk import (
    custom_resources as cr,
    aws_s3 as s3,
    aws_s3_deployment,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_destinations as lambda_destination,
    aws_ssm as ssm,
    aws_sns as sns,
    aws_sqs as sqs,
    aws_sns_subscriptions as sns_subs,
    aws_kms as kms,
    aws_ec2 as ec2,
    aws_sagemaker as sagemaker,
    aws_athena,
    RemovalPolicy,
    Stack,
    Duration,
    CustomResource,
    Tags,
)

from .manager import stack
from .policies.data_policy import DataPolicy
from .policies.service_policy import ServicePolicy
from ... import db
from ...aws.handlers.quicksight import Quicksight
from ...aws.handlers.sagemaker_studio import (
    SagemakerStudio,
)
from ...aws.handlers.sts import SessionHelper
from ...db import models
from ...utils.cdk_nag_utils import CDKNagUtil
from ...utils.runtime_stacks_tagging import TagsUtil

logger = logging.getLogger(__name__)


@stack(stack='environment')
class EnvironmentSetup(Stack):
    module_name = __file__

    def get_engine(self):
        envname = os.environ.get('envname', 'local')
        engine = db.get_engine(envname=envname)
        return engine

    def get_target(self, target_uri) -> models.Environment:
        engine = self.get_engine()
        with engine.scoped_session() as session:
            target = session.query(models.Environment).get(target_uri)
            if not target:
                raise Exception('ObjectNotFound')
        return target

    def get_environment_defautl_vpc(self, engine, environmentUri) -> models.Vpc:
        with engine.scoped_session() as session:
            return db.api.Vpc.get_environment_default_vpc(session, environmentUri)

    def init_quicksight(self, environment: models.Environment):
        Quicksight.create_quicksight_default_group(environment.AwsAccountId)

    def check_sagemaker_studio(self, engine, environment: models.Environment):
        logger.info('check sagemaker studio domain creation')
        existing_domain = SagemakerStudio.get_sagemaker_studio_domain(
            environment.AwsAccountId, environment.region
        )
        existing_domain_id = existing_domain.get('DomainId', False)
        if existing_domain_id:
            return existing_domain_id

    @staticmethod
    def get_environment_group_permissions(engine, environmentUri, group):
        with engine.scoped_session() as session:
            group_permissions = db.api.Environment.list_group_permissions(
                session=session,
                username='cdk',
                groups=None,
                uri=environmentUri,
                data={'groupUri': group},
                check_perm=False,
            )
            permission_names = [permission.name for permission in group_permissions]
            return permission_names

    @staticmethod
    def get_environment_groups(
        engine, environment: models.Environment
    ) -> [models.EnvironmentGroup]:
        with engine.scoped_session() as session:
            return db.api.Environment.list_environment_invited_groups(
                session,
                username='cdk',
                groups=[],
                uri=environment.environmentUri,
                data=None,
                check_perm=False,
            )

    @staticmethod
    def get_environment_admins_group(
        engine, environment: models.Environment
    ) -> [models.EnvironmentGroup]:
        with engine.scoped_session() as session:
            return db.api.Environment.get_environment_group(
                session,
                environment_uri=environment.environmentUri,
                group_uri=environment.SamlGroupName,
            )

    @staticmethod
    def get_environment_group_datasets(
        engine, environment: models.Environment, group: str
    ) -> [models.Dataset]:
        with engine.scoped_session() as session:
            return db.api.Environment.list_group_datasets(
                session,
                username='cdk',
                groups=[],
                uri=environment.environmentUri,
                data={'groupUri': group},
                check_perm=False,
            )

    @staticmethod
    def get_all_environment_datasets(
        engine, environment: models.Environment
    ) -> [models.Dataset]:
        with engine.scoped_session() as session:
            return (
                session.query(models.Dataset)
                .filter(
                    models.Dataset.environmentUri == environment.environmentUri,
                )
                .all()
            )

    def __init__(self, scope, id, target_uri: str = None, **kwargs):
        super().__init__(scope,
                         id,
                         description="Cloud formation stack of ENVIRONMENT: {}; URI: {}; DESCRIPTION: {}".format(
                             self.get_target(target_uri=target_uri).label,
                             target_uri,
                             self.get_target(target_uri=target_uri).description,
                         )[:1024],
                         **kwargs)

        # Required for dynamic stack tagging
        self.target_uri = target_uri

        self.pivot_role_name = SessionHelper.get_delegation_role_name()

        self.engine = self.get_engine()

        self._environment = self.get_target(target_uri=target_uri)

        self.environment_groups: [models.EnvironmentGroup] = self.get_environment_groups(self.engine, environment=self._environment)

        self.environment_admins_group: models.EnvironmentGroup = self.get_environment_admins_group(self.engine, self._environment)

        self.all_environment_datasets = self.get_all_environment_datasets(
            self.engine, self._environment
        )

        self.sagemaker_domain_exists = self.check_sagemaker_studio(engine=self.engine, environment=self._environment)

        if self._environment.mlStudiosEnabled and not(self.sagemaker_domain_exists):

            sagemaker_domain_role = iam.Role(
                self,
                'RoleForSagemakerStudioUsers',
                assumed_by=iam.ServicePrincipal('sagemaker.amazonaws.com'),
                role_name="RoleSagemakerStudioUsers",
                managed_policies=[iam.ManagedPolicy.from_managed_policy_arn(
                    self,
                    id="SagemakerFullAccess",
                    managed_policy_arn="arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"),
                    iam.ManagedPolicy.from_managed_policy_arn(
                    self,
                        id="S3FullAccess",
                        managed_policy_arn="arn:aws:iam::aws:policy/AmazonS3FullAccess")
                ]
            )

            sagemaker_domain_key = kms.Key(
                self,
                'SagemakerDomainKmsKey',
                alias="SagemakerStudioDomain",
                enable_key_rotation=True,
                policy=iam.PolicyDocument(
                    assign_sids=True,
                    statements=[
                        iam.PolicyStatement(
                            resources=['*'],
                            effect=iam.Effect.ALLOW,
                            principals=[
                                iam.AccountPrincipal(account_id=self._environment.AwsAccountId),
                                iam.Role.from_role_arn(self, 'DomainRole', role_arn=sagemaker_domain_role.role_arn),
                                iam.Role.from_role_arn(self, 'EnvironmentDefaultRole', role_arn=self.environment_admins_group.environmentIAMRoleArn),
                            ] + [iam.Role.from_role_arn(self, f'{group.groupUri}Role', role_arn=group.environmentIAMRoleArn) for group in self.environment_groups],
                            actions=['kms:*'],
                        )
                    ],
                ),
            )

            try:
                default_vpc = ec2.Vpc.from_lookup(self, 'VPCStudio', is_default=True)
                vpc_id = default_vpc.vpc_id
                subnet_ids = [private_subnet.subnet_id for private_subnet in default_vpc.private_subnets]
                subnet_ids += [public_subnet.subnet_id for public_subnet in default_vpc.public_subnets]
                subnet_ids += [isolated_subnet.subnet_id for isolated_subnet in default_vpc.isolated_subnets]
            except Exception as e:
                logger.error(f"Default VPC not found, Exception: {e}. If you don't own a default VPC, modify the networking configuration, or disable ML Studio upon environment creation.")

            sagemaker_domain = sagemaker.CfnDomain(
                self,
                "SagemakerStudioDomain",
                domain_name=f"SagemakerStudioDomain-{self._environment.region}-{self._environment.AwsAccountId}",
                auth_mode="IAM",

                default_user_settings=sagemaker.CfnDomain.UserSettingsProperty(
                    execution_role=sagemaker_domain_role.role_arn,

                    security_groups=[],

                    sharing_settings=sagemaker.CfnDomain.SharingSettingsProperty(
                        notebook_output_option="Allowed",
                        s3_kms_key_id=sagemaker_domain_key.key_id,
                        s3_output_path=f"s3://sagemaker-{self._environment.region}-{self._environment.AwsAccountId}",
                    )
                ),

                vpc_id=vpc_id,
                subnet_ids=subnet_ids,
                app_network_access_type="VpcOnly",
                kms_key_id=sagemaker_domain_key.key_id,
            )

            ssm.StringParameter(
                self,
                'SagemakerStudioDomainId',
                string_value=sagemaker_domain.attr_domain_id,
                parameter_name=f'/datahub/{self._environment.environmentUri}/sagemaker/sagemakerstudio/domain_id',
            )

        if self._environment.dashboardsEnabled:
            logger.warning('ensure_quicksight_default_group')
            self.init_quicksight(environment=self._environment)

        self.create_or_import_environment_groups_roles()

        central_account = SessionHelper.get_account()

        default_environment_bucket = s3.Bucket(
            self,
            'EnvironmentDefaultBucket',
            bucket_name=self._environment.EnvironmentDefaultBucketName,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.RETAIN,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
            enforce_ssl=True,
        )
        default_environment_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid='RedshiftLogging',
                actions=['s3:PutObject', 's3:GetBucketAcl'],
                resources=[
                    f'{default_environment_bucket.bucket_arn}/*',
                    default_environment_bucket.bucket_arn,
                ],
                principals=[iam.ServicePrincipal('redshift.amazonaws.com')],
            )
        )

        default_environment_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid='AWSLogDeliveryWrite',
                effect=iam.Effect.ALLOW,
                principals=[iam.ServicePrincipal('logging.s3.amazonaws.com')],
                actions=['s3:PutObject', 's3:PutObjectAcl'],
                resources=[f'{default_environment_bucket.bucket_arn}/*'],
            )
        )

        default_environment_bucket.add_lifecycle_rule(
            abort_incomplete_multipart_upload_after=Duration.days(7),
            noncurrent_version_transitions=[
                s3.NoncurrentVersionTransition(
                    storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                    transition_after=Duration.days(30),
                ),
                s3.NoncurrentVersionTransition(
                    storage_class=s3.StorageClass.GLACIER,
                    transition_after=Duration.days(60),
                ),
            ],
            transitions=[
                s3.Transition(
                    storage_class=s3.StorageClass.INTELLIGENT_TIERING,
                    transition_after=Duration.days(90),
                ),
                s3.Transition(
                    storage_class=s3.StorageClass.GLACIER,
                    transition_after=Duration.days(360),
                ),
            ],
            enabled=True,
        )

        profiling_assetspath = self.zip_code(
            os.path.realpath(
                os.path.abspath(
                    os.path.join(__file__, '..', '..', 'assets', 'glueprofilingjob')
                )
            )
        )

        aws_s3_deployment.BucketDeployment(
            self,
            f'{self._environment.resourcePrefix}GlueProflingJobDeployment',
            sources=[aws_s3_deployment.Source.asset(profiling_assetspath)],
            destination_bucket=default_environment_bucket,
            destination_key_prefix='profiling/code',
        )

        self.create_or_import_environment_default_role()

        self.create_default_athena_workgroup(
            default_environment_bucket,
            self._environment.EnvironmentDefaultAthenaWorkGroup,
        )

        pivot_role = iam.Role.from_role_arn(
            self,
            f'PivotRole{self._environment.environmentUri}',
            f'arn:aws:iam::{self._environment.AwsAccountId}:role/{self.pivot_role_name}',
        )

        # Lakeformation default settings
        entry_point = str(
            pathlib.PosixPath(
                os.path.dirname(__file__), '../assets/lakeformationdefaultsettings'
            ).resolve()
        )

        lakeformation_cr_dlq = self.set_dlq(
            f'{self._environment.resourcePrefix}-lfcr-{self._environment.environmentUri}'
        )
        lf_default_settings_custom_resource = _lambda.Function(
            self,
            'LakeformationDefaultSettingsHandler',
            function_name=f'{self._environment.resourcePrefix}-lf-settings-handler-{self._environment.environmentUri}',
            role=pivot_role,
            handler='index.on_event',
            code=_lambda.Code.from_asset(entry_point),
            memory_size=1664,
            description='This Lambda function is a cloudformation custom resource provider for Lakeformation default settings',
            timeout=Duration.seconds(5 * 60),
            environment={
                'envname': self._environment.name,
                'LOG_LEVEL': 'DEBUG',
                'AWS_ACCOUNT': self._environment.AwsAccountId,
                'DEFAULT_ENV_ROLE_ARN': self._environment.EnvironmentDefaultIAMRoleArn,
                'DEFAULT_CDK_ROLE_ARN': self._environment.CDKRoleArn,
            },
            dead_letter_queue_enabled=True,
            dead_letter_queue=lakeformation_cr_dlq,
            on_failure=lambda_destination.SqsDestination(lakeformation_cr_dlq),
            runtime=_lambda.Runtime.PYTHON_3_9,
        )

        ssm.StringParameter(
            self,
            'LakeformationDefaultSettingsCustomeResourceFunctionArn',
            string_value=lf_default_settings_custom_resource.function_arn,
            parameter_name=f'/dataall/{self._environment.environmentUri}/cfn/lf/defaultsettings/lambda/arn',
        )

        ssm.StringParameter(
            self,
            'LakeformationDefaultSettingsCustomeResourceFunctionName',
            string_value=lf_default_settings_custom_resource.function_name,
            parameter_name=f'/dataall/{self._environment.environmentUri}/cfn/lf/defaultsettings/lambda/name',
        )

        # Glue database custom resource

        entry_point = str(
            pathlib.PosixPath(
                os.path.dirname(__file__), '../assets/gluedatabasecustomresource'
            ).resolve()
        )

        gluedb_cr_dlq = self.set_dlq(
            f'{self._environment.resourcePrefix}-gluedbcr-{self._environment.environmentUri}'
        )
        gluedb_custom_resource = _lambda.Function(
            self,
            'GlueDatabaseCustomResourceHandler',
            function_name=f'{self._environment.resourcePrefix}-gluedb-handler-{self._environment.environmentUri}',
            role=pivot_role,
            handler='index.on_event',
            code=_lambda.Code.from_asset(entry_point),
            memory_size=1664,
            description='This Lambda function is a cloudformation custom resource provider for Glue database '
            'as Cfn currently does not support the CreateTableDefaultPermissions parameter',
            timeout=Duration.seconds(5 * 60),
            environment={
                'envname': self._environment.name,
                'LOG_LEVEL': 'DEBUG',
                'AWS_ACCOUNT': self._environment.AwsAccountId,
                'DEFAULT_ENV_ROLE_ARN': self._environment.EnvironmentDefaultIAMRoleArn,
                'DEFAULT_CDK_ROLE_ARN': self._environment.CDKRoleArn,
            },
            dead_letter_queue_enabled=True,
            dead_letter_queue=gluedb_cr_dlq,
            on_failure=lambda_destination.SqsDestination(gluedb_cr_dlq),
            tracing=_lambda.Tracing.ACTIVE,
            runtime=_lambda.Runtime.PYTHON_3_9,
        )

        ssm.StringParameter(
            self,
            'GlueCustomResourceFunctionArn',
            string_value=gluedb_custom_resource.function_arn,
            parameter_name=f'/dataall/{self._environment.environmentUri}/cfn/custom-resources/lambda/arn',
        )

        ssm.StringParameter(
            self,
            'GlueCustomResourceFunctionName',
            string_value=gluedb_custom_resource.function_name,
            parameter_name=f'/dataall/{self._environment.environmentUri}/cfn/custom-resources/lambda/name',
        )

        LakeformationDefaultSettingsProvider = cr.Provider(
            self,
            f'{self._environment.resourcePrefix}LakeformationDefaultSettingsProvider',
            on_event_handler=lf_default_settings_custom_resource,
        )

        default_lf_settings = CustomResource(
            self,
            f'{self._environment.resourcePrefix}DefaultLakeFormationSettings',
            service_token=LakeformationDefaultSettingsProvider.service_token,
            resource_type='Custom::LakeformationDefaultSettings',
            properties={
                'DataLakeAdmins': [
                    f'arn:aws:iam::{self._environment.AwsAccountId}:role/{self.pivot_role_name}',
                ]
            },
        )

        self.create_athena_workgroups(
            self.environment_groups, default_environment_bucket
        )

        if self._environment.subscriptionsEnabled:
            queue_key = kms.Key(
                self,
                f'{self._environment.resourcePrefix}-producers-queue-key',
                removal_policy=RemovalPolicy.DESTROY,
                alias=f'{self._environment.resourcePrefix}-producers-queue-key',
                enable_key_rotation=True,
            )
            dlq_queue = sqs.Queue(
                self,
                f'ProducersSubscriptionsQueue-{self._environment.environmentUri}-dlq',
                queue_name=f'{self._environment.resourcePrefix}-producers-dlq-{self._environment.environmentUri}',
                retention_period=Duration.days(14),
                encryption=sqs.QueueEncryption.KMS,
                encryption_master_key=queue_key,
            )
            dlq_queue.add_to_resource_policy(
                iam.PolicyStatement(
                    sid='Enforce TLS for all principals',
                    effect=iam.Effect.DENY,
                    principals=[
                        iam.AnyPrincipal(),
                    ],
                    actions=[
                        'sqs:*',
                    ],
                    resources=[dlq_queue.queue_arn],
                    conditions={
                        'Bool': {'aws:SecureTransport': 'false'},
                    },
                )
            )
            self.dlq = sqs.DeadLetterQueue(max_receive_count=2, queue=dlq_queue)
            queue = sqs.Queue(
                self,
                f'ProducersSubscriptionsQueue-{self._environment.environmentUri}',
                queue_name=f'{self._environment.resourcePrefix}-producers-queue-{self._environment.environmentUri}',
                dead_letter_queue=self.dlq,
                encryption=sqs.QueueEncryption.KMS,
                encryption_master_key=queue_key,
            )

            if self._environment.subscriptionsProducersTopicImported:
                topic = sns.Topic.from_topic_arn(
                    self,
                    'ProducersTopicImported',
                    f'arn:aws:sns:{self._environment.region}:{self._environment.AwsAccountId}:{self._environment.subscriptionsProducersTopicName}',
                )
            else:
                topic = self.create_topic(
                    self._environment.subscriptionsProducersTopicName,
                    central_account,
                    self._environment,
                )

            topic.add_subscription(sns_subs.SqsSubscription(queue))

            policy = sqs.QueuePolicy(
                self,
                f'{self._environment.resourcePrefix}ProducersSubscriptionsQueuePolicy',
                queues=[queue],
            )

            policy.document.add_statements(
                iam.PolicyStatement(
                    principals=[iam.AccountPrincipal(central_account)],
                    effect=iam.Effect.ALLOW,
                    actions=[
                        'sqs:ReceiveMessage',
                        'sqs:DeleteMessage',
                        'sqs:ChangeMessageVisibility',
                        'sqs:GetQueueUrl',
                        'sqs:GetQueueAttributes',
                    ],
                    resources=[queue.queue_arn],
                ),
                iam.PolicyStatement(
                    principals=[iam.ServicePrincipal('sns.amazonaws.com')],
                    effect=iam.Effect.ALLOW,
                    actions=['sqs:SendMessage'],
                    resources=[queue.queue_arn],
                    conditions={'ArnEquals': {'aws:SourceArn': topic.topic_arn}},
                ),
                iam.PolicyStatement(
                    sid='Enforce TLS for all principals',
                    effect=iam.Effect.DENY,
                    principals=[
                        iam.AnyPrincipal(),
                    ],
                    actions=[
                        'sqs:*',
                    ],
                    resources=[queue.queue_arn],
                    conditions={
                        'Bool': {'aws:SecureTransport': 'false'},
                    },
                ),
            )
            policy.node.add_dependency(topic)

            self.create_topic(
                self._environment.subscriptionsConsumersTopicName,
                central_account,
                self._environment,
            )

        TagsUtil.add_tags(self)

        CDKNagUtil.check_rules(self)

    def create_or_import_environment_default_role(self):
        if self._environment.EnvironmentDefaultIAMRoleImported:
            default_role = iam.Role.from_role_arn(
                self,
                f'EnvironmentRole{self._environment.environmentUri}Imported',
                self._environment.EnvironmentDefaultIAMRoleArn,
            )
        else:
            services_policies = ServicePolicy(
                stack=self,
                tag_key='Team',
                tag_value=self._environment.SamlGroupName,
                resource_prefix=self._environment.resourcePrefix,
                name=f'{self._environment.resourcePrefix}-{self._environment.SamlGroupName}-default-services-policy',
                id=f'{self._environment.resourcePrefix}-{self._environment.SamlGroupName}-default-services-policy',
                account=self._environment.AwsAccountId,
                region=self._environment.region,
                role_name=self._environment.EnvironmentDefaultIAMRoleName,
                permissions=self.get_environment_group_permissions(
                    self.engine,
                    self._environment.environmentUri,
                    self._environment.SamlGroupName,
                ),
            ).generate_policies()

            data_policy = DataPolicy(
                stack=self,
                tag_key='Team',
                tag_value=self._environment.SamlGroupName,
                resource_prefix=self._environment.resourcePrefix,
                name=f'{self._environment.resourcePrefix}-{self._environment.SamlGroupName}-default-data-policy',
                id=f'{self._environment.resourcePrefix}-{self._environment.SamlGroupName}-default-data-policy',
                account=self._environment.AwsAccountId,
                region=self._environment.region,
                environment=self._environment,
                team=self.environment_admins_group,
                datasets=self.all_environment_datasets,
            ).generate_admins_data_access_policy()

            default_role = iam.Role(
                self,
                'DefaultEnvironmentRole',
                role_name=self._environment.EnvironmentDefaultIAMRoleName,
                inline_policies={
                    f'DataPolicy{self._environment.environmentUri}': data_policy.document,
                },
                managed_policies=services_policies,
                assumed_by=iam.CompositePrincipal(
                    iam.ServicePrincipal('glue.amazonaws.com'),
                    iam.ServicePrincipal('lambda.amazonaws.com'),
                    iam.ServicePrincipal('lakeformation.amazonaws.com'),
                    iam.ServicePrincipal('athena.amazonaws.com'),
                    iam.ServicePrincipal('states.amazonaws.com'),
                    iam.ServicePrincipal('sagemaker.amazonaws.com'),
                    iam.ServicePrincipal('redshift.amazonaws.com'),
                    iam.ServicePrincipal('databrew.amazonaws.com'),
                    iam.AccountPrincipal(self._environment.AwsAccountId),
                ),
            )
        return default_role

    def create_or_import_environment_groups_roles(self):
        group: models.EnvironmentGroup
        for group in self.environment_groups:
            if not group.environmentIAMRoleImported:
                self.create_group_environment_role(group)
            else:
                iam.Role.from_role_arn(
                    self,
                    f'{group.groupUri + group.environmentIAMRoleName}',
                    role_arn=f'arn:aws:iam::{self.environment.AwsAccountId}:role/{group.environmentIAMRoleName}',
                )

    def create_group_environment_role(self, group):

        group_permissions = self.get_environment_group_permissions(
            self.engine, self._environment.environmentUri, group.groupUri
        )
        services_policies = ServicePolicy(
            stack=self,
            tag_key='Team',
            tag_value=group.groupUri,
            resource_prefix=self._environment.resourcePrefix,
            name=f'{self._environment.resourcePrefix}-{group.groupUri}-services-policy',
            id=f'{self._environment.resourcePrefix}-{group.groupUri}-services-policy',
            role_name=group.environmentIAMRoleName,
            account=self._environment.AwsAccountId,
            region=self._environment.region,
            permissions=group_permissions,
        ).generate_policies()

        data_policy = DataPolicy(
            stack=self,
            tag_key='Team',
            tag_value=group.groupUri,
            resource_prefix=self._environment.resourcePrefix,
            name=f'{self._environment.resourcePrefix}-{group.groupUri}-data-policy',
            id=f'{self._environment.resourcePrefix}-{group.groupUri}-data-policy',
            account=self._environment.AwsAccountId,
            region=self._environment.region,
            environment=self._environment,
            team=group,
            datasets=self.get_environment_group_datasets(
                self.engine, self._environment, group.groupUri
            ),
        ).generate_data_access_policy()

        group_role = iam.Role(
            self,
            f'{group.environmentIAMRoleName}',
            role_name=group.environmentIAMRoleName,
            inline_policies={
                f'{group.environmentIAMRoleName}DataPolicy': data_policy.document,
            },
            managed_policies=services_policies,
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal('glue.amazonaws.com'),
                iam.ServicePrincipal('lambda.amazonaws.com'),
                iam.ServicePrincipal('lakeformation.amazonaws.com'),
                iam.ServicePrincipal('athena.amazonaws.com'),
                iam.ServicePrincipal('states.amazonaws.com'),
                iam.ServicePrincipal('sagemaker.amazonaws.com'),
                iam.ServicePrincipal('redshift.amazonaws.com'),
                iam.AccountPrincipal(self._environment.AwsAccountId),
            ),
        )
        Tags.of(group_role).add('group', group.groupUri)
        return group_role

    def create_default_athena_workgroup(self, output_bucket, workgroup_name):
        return self.create_athena_workgroup(output_bucket, workgroup_name)

    def create_athena_workgroups(self, environment_groups, default_environment_bucket):
        for group in environment_groups:
            self.create_athena_workgroup(
                default_environment_bucket, group.environmentAthenaWorkGroup
            )

    def create_athena_workgroup(self, output_bucket, workgroup_name):
        athena_workgroup_output_location = ''.join(
            ['s3://', output_bucket.bucket_name, '/athenaqueries/', workgroup_name, '/']
        )
        athena_workgroup = aws_athena.CfnWorkGroup(
            self,
            f'AthenaWorkGroup{workgroup_name}',
            name=workgroup_name,
            state='ENABLED',
            recursive_delete_option=True,
            work_group_configuration=aws_athena.CfnWorkGroup.WorkGroupConfigurationProperty(
                enforce_work_group_configuration=True,
                result_configuration=aws_athena.CfnWorkGroup.ResultConfigurationProperty(
                    encryption_configuration=aws_athena.CfnWorkGroup.EncryptionConfigurationProperty(
                        encryption_option='SSE_S3',
                    ),
                    output_location=athena_workgroup_output_location,
                ),
                requester_pays_enabled=False,
                publish_cloud_watch_metrics_enabled=False,
                engine_version=aws_athena.CfnWorkGroup.EngineVersionProperty(
                    selected_engine_version='Athena engine version 2',
                ),
            ),
        )
        return athena_workgroup

    def create_topic(self, construct_id, central_account, environment):
        actions = [
            'SNS:GetTopicAttributes',
            'SNS:SetTopicAttributes',
            'SNS:AddPermission',
            'SNS:RemovePermission',
            'SNS:DeleteTopic',
            'SNS:Subscribe',
            'SNS:ListSubscriptionsByTopic',
            'SNS:Publish',
            'SNS:Receive',
        ]
        topic_key = kms.Key(
            self,
            f'{construct_id}-topic-key',
            removal_policy=RemovalPolicy.DESTROY,
            alias=f'{construct_id}-topic-key',
            enable_key_rotation=True,
        )
        topic = sns.Topic(
            self, f'{construct_id}', topic_name=f'{construct_id}', master_key=topic_key
        )
        topic.add_to_resource_policy(
            iam.PolicyStatement(
                principals=[iam.AccountPrincipal(central_account)],
                effect=iam.Effect.ALLOW,
                actions=actions,
                resources=[topic.topic_arn],
            )
        )
        topic.add_to_resource_policy(
            iam.PolicyStatement(
                principals=[iam.AccountPrincipal(environment.AwsAccountId)],
                effect=iam.Effect.ALLOW,
                actions=actions,
                resources=[topic.topic_arn],
            )
        )
        return topic

    @staticmethod
    def zip_code(assetspath, s3_key='profiler'):
        logger.info('Zipping code')
        shutil.make_archive(
            base_name=f'{assetspath}/{s3_key}', format='zip', root_dir=f'{assetspath}'
        )
        return assetspath

    def set_dlq(self, queue_name) -> sqs.Queue:
        queue_key = kms.Key(
            self,
            f'{queue_name}-key',
            removal_policy=RemovalPolicy.DESTROY,
            alias=f'{queue_name}-key',
            enable_key_rotation=True,
        )

        dlq = sqs.Queue(
            self,
            f'{queue_name}-queue',
            queue_name=f'{queue_name}',
            retention_period=Duration.days(14),
            encryption=sqs.QueueEncryption.KMS,
            encryption_master_key=queue_key,
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
