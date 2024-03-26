from aws_cdk import (
    aws_ssm as ssm,
    aws_sqs as sqs,
    aws_kms as kms,
    aws_iam as iam,
    RemovalPolicy,
    Duration,
)

from .pyNestedStack import pyNestedClass


class SqsStack(pyNestedClass):
    def __init__(
        self,
        scope,
        id,
        envname='dev',
        resource_prefix='dataall',
        prod_sizing=False,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)
        self.queue_key = kms.Key(
            self,
            f'{resource_prefix}-{envname}-queue-key',
            removal_policy=RemovalPolicy.DESTROY,
            alias=f'{resource_prefix}-{envname}-queue-key',
            enable_key_rotation=True,
        )

        dlq_queue = sqs.Queue(
            self,
            f'{resource_prefix}-{envname}-dlq-queue',
            queue_name=f'{resource_prefix}-{envname}-dlq-queue.fifo',
            fifo=True,
            retention_period=Duration.days(14),
            encryption=sqs.QueueEncryption.KMS,
            encryption_master_key=self.queue_key,
            data_key_reuse=Duration.days(1),
            removal_policy=RemovalPolicy.DESTROY,
        )

        dlq_queue.add_to_resource_policy(self.get_enforce_ssl_policy(dlq_queue.queue_arn))

        self.dlq = sqs.DeadLetterQueue(
            max_receive_count=1,
            queue=dlq_queue,
        )

        self.queue = sqs.Queue(
            self,
            f'{resource_prefix}-{envname}-queue',
            queue_name=f'{resource_prefix}-{envname}-queue.fifo',
            dead_letter_queue=self.dlq,
            fifo=True,
            encryption=sqs.QueueEncryption.KMS,
            encryption_master_key=self.queue_key,
            retention_period=Duration.days(14),
            data_key_reuse=Duration.days(1),
            removal_policy=RemovalPolicy.DESTROY,
            visibility_timeout=Duration.seconds(900),
        )

        self.queue.add_to_resource_policy(self.get_enforce_ssl_policy(self.queue.queue_arn))

        ssm.StringParameter(
            self,
            'SqsQueueParameter',
            parameter_name=f'/dataall/{envname}/sqs/queue_name',
            string_value=self.queue.queue_name,
        )

        ssm.StringParameter(
            self,
            'SqsQueueUrlParameter',
            parameter_name=f'/dataall/{envname}/sqs/queue_url',
            string_value=self.queue.queue_url,
        )

    def get_enforce_ssl_policy(self, queue_arn):
        return iam.PolicyStatement(
            sid='Enforce TLS for all principals',
            effect=iam.Effect.DENY,
            principals=[
                iam.AnyPrincipal(),
            ],
            actions=[
                'sqs:*',
            ],
            resources=[queue_arn],
            conditions={
                'Bool': {'aws:SecureTransport': 'false'},
            },
        )
