from aws_cdk import (
    aws_kms as kms,
    aws_sns as sns,
    aws_ses as ses,
    aws_route53 as route53,
    aws_iam as iam,
    RemovalPolicy,
)


from .pyNestedStack import pyNestedClass


class SesStack(pyNestedClass):
    def __init__(
        self,
        scope,
        id,
        envname='dev',
        resource_prefix='dataall',
        custom_domain=None,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)
        configuration_set_name = f'{resource_prefix}-{envname}-ses-configuration-set'
        self.KMS_SNS = kms.Key(
            self,
            f'{resource_prefix}-{envname}-SNS-key',
            removal_policy=RemovalPolicy.DESTROY,
            alias=f'{resource_prefix}-{envname}-SNS-key',
            enable_key_rotation=True,
        )

        self.KMS_SNS.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=['kms:Decrypt', 'kms:GenerateDataKey*'],
                principals=[iam.ServicePrincipal('ses.amazonaws.com')],
                resources=['*'],
                conditions={
                    'StringLike': {
                        'aws:SourceArn': f'arn:aws:ses:{self.region}:{self.account}:configuration-set/{configuration_set_name}'
                    }
                },
            )
        )

        self.sns = sns.Topic(
            self,
            f'{resource_prefix}-{envname}-SNS-Email-Bounce-Topic',
            display_name='SNS-Email-Bounce-Topic',
            topic_name=f'{resource_prefix}-{envname}-SNS-Email-Bounce-Topic',
            master_key=self.KMS_SNS,
        )

        self.sns.apply_removal_policy(RemovalPolicy.DESTROY)

        self.configuration_set = ses.ConfigurationSet(
            self,
            f'{resource_prefix}-{envname}-SES-Configuration-Set',
            configuration_set_name=configuration_set_name,
            tls_policy=ses.ConfigurationSetTlsPolicy.REQUIRE,
        )

        self.configuration_set.add_event_destination(
            'SNS-On-Bounce',
            destination=ses.EventDestination.sns_topic(self.sns),
            events=[
                ses.EmailSendingEvent.BOUNCE,
                ses.EmailSendingEvent.DELIVERY_DELAY,
                ses.EmailSendingEvent.REJECT,
                ses.EmailSendingEvent.COMPLAINT,
            ],
        )

        self.configuration_set.apply_removal_policy(RemovalPolicy.DESTROY)

        hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
            self,
            'data-all-hosted-zone',
            zone_name=custom_domain.get('hosted_zone_name'),
            hosted_zone_id=custom_domain.get('hosted_zone_id'),
        )

        self.ses_identity = ses.EmailIdentity(
            self,
            id=f'{resource_prefix}-{envname}-SES-Identity',
            identity=ses.Identity.public_hosted_zone(hosted_zone),
            configuration_set=self.configuration_set,
        )

        self.ses_identity.apply_removal_policy(RemovalPolicy.DESTROY)
