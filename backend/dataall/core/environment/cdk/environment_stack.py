import logging
import os
from abc import abstractmethod
from typing import List, Type

from aws_cdk import (
    aws_s3 as s3,
    aws_iam as iam,
    aws_sns as sns,
    aws_sqs as sqs,
    aws_sns_subscriptions as sns_subs,
    aws_kms as kms,
    aws_athena,
    RemovalPolicy,
    CfnOutput,
    Stack,
    Duration,
    Tags,
)

from dataall.core.stacks.services.runtime_stacks_tagging import TagsUtil
from dataall.core.environment.db.environment_models import Environment, EnvironmentGroup
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.environment.services.managed_iam_policies import PolicyManager
from dataall.core.environment.api.enums import EnvironmentType
from dataall.base.cdkproxy.stacks.manager import stack
from dataall.core.environment.cdk.pivot_role_stack import PivotRole
from dataall.core.environment.cdk.cdk_asset_trail import setup_cdk_asset_trail
from dataall.core.environment.cdk.env_role_core_policies.data_policy import S3Policy
from dataall.core.environment.cdk.env_role_core_policies.service_policy import ServicePolicy
from dataall.base import db
from dataall.base.aws.parameter_store import ParameterStoreManager
from dataall.base.aws.sts import SessionHelper
from dataall.base.utils.cdk_nag_utils import CDKNagUtil

logger = logging.getLogger(__name__)


class EnvironmentStackExtension:
    @staticmethod
    @abstractmethod
    def extent(setup: 'EnvironmentSetup'):
        raise NotImplementedError


@stack(stack='environment')
class EnvironmentSetup(Stack):
    """Deploy common environment resources:
        - default environment S3 Bucket
        - SSM parameters for the Lambdas and Providers
        - pivotRole (if configured)
        - SNS topic (if subscriptions are enabled)
        - Module extension stacks (if module is enabled and has an associated extension stack)
    - Deploy team specific resources: teams IAM roles, Athena workgroups
    - Set PivotRole as Lake formation data lake Admin - lakeformationdefaultsettings custom resource
    """

    module_name = __file__
    _EXTENSIONS: List[Type[EnvironmentStackExtension]] = []

    @staticmethod
    def register(extension: Type[EnvironmentStackExtension]):
        EnvironmentSetup._EXTENSIONS.append(extension)

    def environment(self) -> Environment:
        return self._environment

    @staticmethod
    def get_env_name():
        return os.environ.get('envname', 'local')

    def get_engine(self):
        engine = db.get_engine(envname=self.get_env_name())
        return engine

    def get_target(self, target_uri) -> Environment:
        engine = self.get_engine()
        with engine.scoped_session() as session:
            target = session.query(Environment).get(target_uri)
            if not target:
                raise Exception('ObjectNotFound')
        return target

    @staticmethod
    def get_environment_group_permissions(engine, environmentUri, group):
        with engine.scoped_session() as session:
            group_permissions = EnvironmentService.list_group_permissions_internal(
                session=session, uri=environmentUri, group_uri=group
            )
            permission_names = [permission.name for permission in group_permissions]
            return permission_names

    @staticmethod
    def get_environment_groups(engine, environment: Environment) -> [EnvironmentGroup]:
        with engine.scoped_session() as session:
            return EnvironmentService.list_environment_invited_groups(
                session,
                uri=environment.environmentUri,
            )

    @staticmethod
    def get_environment_admins_group(engine, environment: Environment) -> [EnvironmentGroup]:
        with engine.scoped_session() as session:
            return EnvironmentService.get_environment_group(
                session,
                environment_uri=environment.environmentUri,
                group_uri=environment.SamlGroupName,
            )

    def __init__(self, scope, id, target_uri: str = None, **kwargs):
        super().__init__(
            scope,
            id,
            description='Cloud formation stack of ENVIRONMENT: {}; URI: {}; DESCRIPTION: {}'.format(
                self.get_target(target_uri=target_uri).label,
                target_uri,
                self.get_target(target_uri=target_uri).description,
            )[:1024],
            **kwargs,
        )
        # Read input
        self.target_uri = target_uri
        self.external_id = SessionHelper.get_external_id_secret()
        self.dataall_central_account = SessionHelper.get_account()

        pivot_role_as_part_of_environment_stack = ParameterStoreManager.get_parameter_value(
            region=os.getenv('AWS_REGION', 'eu-west-1'),
            parameter_path=f'/dataall/{os.getenv("envname", "local")}/pivotRole/enablePivotRoleAutoCreate',
        )
        self.create_pivot_role = True if pivot_role_as_part_of_environment_stack == 'True' else False
        self.engine = self.get_engine()

        self._environment = self.get_target(target_uri=target_uri)
        self.pivot_role_name = SessionHelper.get_delegation_role_name(region=self._environment.region)

        self.environment_groups: [EnvironmentGroup] = self.get_environment_groups(
            self.engine, environment=self._environment
        )

        self.environment_admins_group: EnvironmentGroup = self.get_environment_admins_group(
            self.engine, self._environment
        )
        # Create test role for integration tests
        if self._environment.environmentType == EnvironmentType.IntegrationTesting.value:
            self.create_integration_tests_role()

        # Create or import Pivot role
        if self.create_pivot_role is True:
            config = {
                'roleName': self.pivot_role_name,
                'accountId': self.dataall_central_account,
                'externalId': self.external_id,
                'resourcePrefix': self._environment.resourcePrefix,
                'environmentUri': self._environment.environmentUri,
            }
            pivot_role_stack = PivotRole(self, 'PivotRoleStack', config)
            self.pivot_role = iam.Role.from_role_arn(
                self,
                f'PivotRole{self._environment.environmentUri}',
                pivot_role_stack.pivot_role.role_arn,
            )
        else:
            self.pivot_role = iam.Role.from_role_arn(
                self,
                f'PivotRole{self._environment.environmentUri}',
                f'arn:aws:iam::{self._environment.AwsAccountId}:role/{self.pivot_role_name}',
            )

        # Environment Logging S3 Bucket
        default_environment_log_bucket = s3.Bucket(
            self,
            'EnvironmentDefaultLogBucket',
            bucket_name=self._environment.EnvironmentLogsBucketName,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.RETAIN,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
            enforce_ssl=True,
        )
        default_environment_log_bucket.policy.apply_removal_policy(RemovalPolicy.RETAIN)
        default_environment_log_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid='AWSLogDeliveryWrite',
                effect=iam.Effect.ALLOW,
                principals=[iam.ServicePrincipal('logging.s3.amazonaws.com')],
                actions=['s3:PutObject', 's3:PutObjectAcl'],
                resources=[f'{default_environment_log_bucket.bucket_arn}/*'],
            )
        )

        setup_cdk_asset_trail(self, default_environment_log_bucket)

        # Environment S3 Bucket
        default_environment_bucket = s3.Bucket(
            self,
            'EnvironmentDefaultBucket',
            bucket_name=self._environment.EnvironmentDefaultBucketName,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.RETAIN,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
            enforce_ssl=True,
            server_access_logs_bucket=default_environment_log_bucket,
            server_access_logs_prefix=f'access_logs/{self._environment.EnvironmentDefaultBucketName}/',
        )
        default_environment_bucket.policy.apply_removal_policy(RemovalPolicy.RETAIN)
        self.default_environment_bucket = default_environment_bucket

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

        # Create or import team IAM roles
        self.default_role = self.create_or_import_environment_admin_group_role()
        self.group_roles = self.create_or_import_environment_groups_roles()

        self.create_default_athena_workgroup(
            default_environment_bucket,
            self._environment.EnvironmentDefaultAthenaWorkGroup,
        )
        self.create_athena_workgroups(self.environment_groups, default_environment_bucket)

        # Create SNS topics for subscriptions
        if self._environment.subscriptionsEnabled:
            subscription_key_policy = iam.PolicyDocument(
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
                        principals=[self.default_role] + self.group_roles,
                        resources=['*'],
                        conditions={
                            'StringEquals': {
                                'kms:ViaService': [
                                    f'sqs.{self._environment.region}.amazonaws.com',
                                    f'sns.{self._environment.region}.amazonaws.com',
                                ]
                            }
                        },
                    ),
                    iam.PolicyStatement(
                        actions=[
                            'kms:DescribeKey',
                            'kms:List*',
                            'kms:GetKeyPolicy',
                        ],
                        effect=iam.Effect.ALLOW,
                        principals=[self.default_role] + self.group_roles,
                        resources=['*'],
                    ),
                ],
            )
            subscription_key = kms.Key(
                self,
                f'dataall-env-{self._environment.environmentUri}-subscription-key',
                removal_policy=RemovalPolicy.DESTROY,
                alias=f'dataall-env-{self._environment.environmentUri}-subscription-key',
                enable_key_rotation=True,
                admins=[
                    iam.ArnPrincipal(self._environment.CDKRoleArn),
                ],
                policy=subscription_key_policy,
            )

            dlq_queue = sqs.Queue(
                self,
                f'ProducersSubscriptionsQueue-{self._environment.environmentUri}-dlq',
                queue_name=f'{self._environment.resourcePrefix}-producers-dlq-{self._environment.environmentUri}',
                retention_period=Duration.days(14),
                encryption=sqs.QueueEncryption.KMS,
                encryption_master_key=subscription_key,
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
                encryption_master_key=subscription_key,
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
                    self.dataall_central_account,
                    self._environment,
                    subscription_key,
                )

            topic.add_subscription(sns_subs.SqsSubscription(queue))

            policy = sqs.QueuePolicy(
                self,
                f'{self._environment.resourcePrefix}ProducersSubscriptionsQueuePolicy',
                queues=[queue],
            )

            policy.document.add_statements(
                iam.PolicyStatement(
                    principals=[iam.AccountPrincipal(self.dataall_central_account)],
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
                self.dataall_central_account,
                self._environment,
                subscription_key,
            )

        # print the IAM role arn for this service account
        CfnOutput(
            self,
            f'pivotRoleName-{self._environment.environmentUri}',
            export_name=f'pivotRoleName-{self._environment.environmentUri}',
            value=self.pivot_role_name,
            description='pivotRole name, helps us to distinguish between auto-created pivot roles (dataallPivotRole-cdk) and manually created pivot roles (dataallPivotRole)',
        )

        for extension in EnvironmentSetup._EXTENSIONS:
            logger.info(f'Adding extension stack{extension.__name__}')
            extension.extent(self)

        TagsUtil.add_tags(stack=self, model=Environment, target_type='environment')

        CDKNagUtil.check_rules(self)

    def create_or_import_environment_admin_group_role(self):
        if self._environment.EnvironmentDefaultIAMRoleImported:
            default_role = iam.Role.from_role_arn(
                self,
                f'EnvironmentRole{self._environment.environmentUri}Imported',
                self._environment.EnvironmentDefaultIAMRoleArn,
            )
            return default_role
        else:
            environment_admin_group_role = self.create_group_environment_role(
                group=self.environment_admins_group, id='DefaultEnvironmentRole'
            )
            return environment_admin_group_role

    def create_or_import_environment_groups_roles(self):
        group: EnvironmentGroup
        group_roles = []
        for group in self.environment_groups:
            if not group.environmentIAMRoleImported:
                group_role = self.create_group_environment_role(group=group, id=f'{group.environmentIAMRoleName}')
            else:
                group_role = iam.Role.from_role_arn(
                    self,
                    f'{group.groupUri + group.environmentIAMRoleName}',
                    role_arn=group.environmentIAMRoleArn,
                )
            group_roles.append(group_role)
        return group_roles

    def create_group_environment_role(self, group: EnvironmentGroup, id: str):
        group_permissions = self.get_environment_group_permissions(
            self.engine, self._environment.environmentUri, group.groupUri
        )
        services_policies = ServicePolicy(
            stack=self,
            tag_key='Team',
            tag_value=group.groupUri,
            resource_prefix=self._environment.resourcePrefix,
            name=f'{self._environment.resourcePrefix}-{group.groupUri}-{self._environment.environmentUri}-services-policy',
            id=f'{self._environment.resourcePrefix}-{group.groupUri}-{self._environment.environmentUri}-services-policy',
            role_name=group.environmentIAMRoleName,
            account=self._environment.AwsAccountId,
            region=self._environment.region,
            environment=self._environment,
            team=group,
            permissions=group_permissions,
        ).generate_policies()

        external_managed_policies = []
        policy_manager = PolicyManager(
            environmentUri=self._environment.environmentUri,
            resource_prefix=self._environment.resourcePrefix,
            role_name=group.environmentIAMRoleName,
            account=self._environment.AwsAccountId,
            region=self._environment.region,
        )
        try:
            managed_policies = policy_manager.get_all_policies()
        except Exception as e:
            logger.info(f'Not adding any managed policy because of exception: {e}')
            # Known exception raised in first deployment because pivot role does not exist and cannot be assumed
            managed_policies = []
        for policy in managed_policies:
            # If there is a managed policy that exist it should be attached to the IAM role
            if policy.get('exists', False):
                external_managed_policies.append(
                    iam.ManagedPolicy.from_managed_policy_name(
                        self,
                        id=f'{self._environment.resourcePrefix}-managed-policy-{policy.get("policy_name")}',
                        managed_policy_name=policy.get('policy_name'),
                    )
                )

        with self.engine.scoped_session() as session:
            data_policy = S3Policy(
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
            ).generate_data_access_policy(session=session)

        group_role = iam.Role(
            self,
            id,
            role_name=group.environmentIAMRoleName,
            inline_policies={
                f'{group.environmentIAMRoleName}DataPolicy': data_policy.document,
            },
            managed_policies=services_policies + external_managed_policies,
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal('glue.amazonaws.com'),
                iam.ServicePrincipal('lambda.amazonaws.com'),
                iam.ServicePrincipal('sagemaker.amazonaws.com'),
                iam.ServicePrincipal('states.amazonaws.com'),
                iam.ServicePrincipal('databrew.amazonaws.com'),
                iam.ServicePrincipal('codebuild.amazonaws.com'),
                iam.ServicePrincipal('codepipeline.amazonaws.com'),
                iam.ServicePrincipal('omics.amazonaws.com'),
                self.pivot_role,
            ),
        )
        Tags.of(group_role).add('group', group.groupUri)
        return group_role

    def create_default_athena_workgroup(self, output_bucket, workgroup_name):
        return self.create_athena_workgroup(output_bucket, workgroup_name)

    def create_athena_workgroups(self, environment_groups, default_environment_bucket):
        for group in environment_groups:
            self.create_athena_workgroup(default_environment_bucket, group.environmentAthenaWorkGroup)

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
                    selected_engine_version='Athena engine version 3',
                ),
            ),
        )
        return athena_workgroup

    def create_topic(self, construct_id, central_account, environment, kms_key):
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
        topic = sns.Topic(self, f'{construct_id}', topic_name=f'{construct_id}', master_key=kms_key)

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

    def create_integration_tests_role(self):
        toolingAccount = ParameterStoreManager.get_parameter_value(
            region=os.getenv('AWS_REGION', 'eu-west-1'),
            parameter_path=f'/dataall/{os.getenv("envname", "local")}/toolingAccount',
        )
        self.test_role = iam.Role(
            self,
            'IntegrationTestRole',
            role_name=f'dataall-integration-tests-role-{self._environment.region}',
            assumed_by=iam.AccountPrincipal(toolingAccount),
        )
        self.test_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    's3:CreateBucket',
                    's3:DeleteBucket',
                    's3:PutEncryptionConfiguration',
                    's3:GetObject*',
                    's3:DeleteObject',
                    's3:DeleteObjectVersion',
                ],
                effect=iam.Effect.ALLOW,
                resources=[
                    'arn:aws:s3:::dataalltesting*',
                    'arn:aws:s3:::dataalltesting*/*',
                    'arn:aws:s3:::dataall-session*',
                    'arn:aws:s3:::dataall-session*/*',
                    'arn:aws:s3:::dataall-test-session*',
                    'arn:aws:s3:::dataall-test-session*/*',
                    'arn:aws:s3:::dataall-temp*',
                    'arn:aws:s3:::dataall-temp*/*',
                    'arn:aws:s3:::dataall-env-access-logs*',
                ],
            )
        )
        self.test_role.add_to_policy(
            iam.PolicyStatement(
                actions=['glue:CreateDatabase', 'glue:DeleteDatabase'],
                effect=iam.Effect.ALLOW,
                resources=[
                    f'arn:aws:glue:{self.region}:{self.account}:catalog',
                    f'arn:aws:glue:{self.region}:{self.account}:database/dataalltesting*',
                    f'arn:aws:glue:{self.region}:{self.account}:table/dataalltesting*',
                    f'arn:aws:glue:{self.region}:{self.account}:userDefinedFunction/dataalltesting*',
                ],
            )
        )
        self.test_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    'lakeformation:GrantPermissions',
                    'lakeformation:RevokePermissions',
                    'lakeformation:PutDataLakeSettings',
                    'lakeformation:GetDataLakeSettings',
                    'glue:GetDatabase',
                    'kms:CreateKey',
                    'kms:CreateAlias',
                    'kms:DeleteAlias',
                    'kms:ListAliases',
                    'kms:GetKeyPolicy',
                    'kms:PutKeyPolicy',
                    'kms:ScheduleKeyDeletion',
                    'kms:TagResource',
                    'kms:DescribeKey',
                    's3:GetBucketVersioning',
                    's3:List*',
                    's3:ListAccessPoints',
                    's3:DeleteAccessPoint',
                ],
                effect=iam.Effect.ALLOW,
                resources=['*'],
            )
        )

        self.test_role.add_to_policy(
            iam.PolicyStatement(
                actions=['ec2:Describe*', 'ec2:*Vpc*', 'ec2:*Subnet*', 'ec2:*Route*', 'ec2:*Tags*'],
                effect=iam.Effect.ALLOW,
                resources=[
                    f'arn:aws:ec2:*:{self.account}:route-table/*',
                    f'arn:aws:ec2:*:{self.account}:security-group/*',
                    f'arn:aws:ec2:*:{self.account}:vpc/*',
                    f'arn:aws:ec2:*:{self.account}:security-group-rule/*',
                    f'arn:aws:ec2:*:{self.account}:subnet/*',
                    f'arn:aws:ec2:*:{self.account}:network-acl/*',
                ],
            ),
        )

        self.test_role.add_to_policy(
            iam.PolicyStatement(
                actions=['ec2:Describe*'],
                effect=iam.Effect.ALLOW,
                resources=['*'],
            ),
        )

        self.test_role.add_to_policy(
            iam.PolicyStatement(
                actions=['cloudformation:Describe*'],
                effect=iam.Effect.ALLOW,
                resources=[f'arn:aws:cloudformation:*:{self.account}:stack/*/*'],
            ),
        )

        self.test_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    'iam:GetRole',
                    'iam:CreateRole',
                    'iam:DeleteRole',
                    'iam:PutRolePolicy',
                    'iam:DeleteRolePolicy',
                    'iam:DetachRolePolicy',
                    'iam:ListAttachedRolePolicies',
                ],
                effect=iam.Effect.ALLOW,
                resources=[
                    f'arn:aws:iam::{self.account}:role/dataall-test*',
                    f'arn:aws:iam::{self.account}:role/dataall-session*',
                ],
            ),
        )

        self.test_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    'quicksight:DescribeAccountSubscription',
                ],
                effect=iam.Effect.ALLOW,
                resources=[f'arn:aws:quicksight:*:{self.account}:*'],
            ),
        )

        self.test_role.add_to_policy(
            iam.PolicyStatement(
                actions=['redshift:DeauthorizeDataShare'],
                effect=iam.Effect.ALLOW,
                resources=[f'arn:aws:redshift:{self.region}:{self.account}:datashare:*/dataall*'],
            ),
        )
