from aws_cdk import aws_codestarnotifications as notifications, RemovalPolicy
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kms as kms
from aws_cdk import aws_sns as sns
from aws_cdk.aws_codestarnotifications import DetailType

from .pyNestedStack import pyNestedClass


class PipelineNotificationStack(pyNestedClass):
    def __init__(
        self,
        scope,
        id,
        git_branch='dev',
        resource_prefix='dataall',
        pipeline=None,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        self.topic_key = kms.Key(
            self,
            f'{resource_prefix}-{git_branch}-alarms-topic-key',
            removal_policy=RemovalPolicy.DESTROY,
            alias=f'{resource_prefix}-{git_branch}-alarms-topic-key',
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
                            iam.ServicePrincipal(service='codestar-notifications.amazonaws.com'),
                        ],
                        actions=['kms:GenerateDataKey*', 'kms:Decrypt'],
                    ),
                ],
            ),
        )

        self.notification_topic = sns.Topic(
            self,
            'Topic',
            topic_name=f'{resource_prefix}-{git_branch}-topic',
            master_key=self.topic_key,
        )

        self.notification_topic.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[
                    iam.ServicePrincipal(service='codestar-notifications.amazonaws.com'),
                ],
                actions=['sns:Publish'],
                resources=['*'],
                conditions={'StringEquals': {'aws:SourceAccount': self.account}},
            )
        )

        self.notification_rule = notifications.NotificationRule(
            self,
            'CodePipelineNotifications',
            detail_type=DetailType.BASIC,
            events=[
                'codepipeline-pipeline-action-execution-failed',
                'codepipeline-pipeline-stage-execution-failed',
                'codepipeline-pipeline-pipeline-execution-failed',
                'codepipeline-pipeline-manual-approval-failed',
                'codepipeline-pipeline-manual-approval-needed',
                'codepipeline-pipeline-pipeline-execution-succeeded',
            ],
            notification_rule_name=f'{resource_prefix}-{git_branch}-pipeline-notifications',
            source=pipeline,
            targets=[self.notification_topic],
            enabled=True,
        )
        self.notification_rule.node.add_dependency(self.notification_topic)
        self.notification_rule.node.add_dependency(pipeline)
