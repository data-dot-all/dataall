from aws_cdk import Stage, Tags, Aspects
from cdk_nag import NagSuppressions, AwsSolutionsChecks, NagPackSuppression

from .albfront_stack import AlbFrontStack
from .cdk_nag_exclusions import ALBFRONT_STACK_CDK_NAG_EXCLUSIONS


class AlbFrontStage(Stage):
    def __init__(
        self,
        scope,
        id: str,
        envname='dev',
        resource_prefix='dataall',
        ecr_repository=None,
        image_tag=None,
        custom_domain=None,
        ip_ranges=None,
        custom_auth=None,
        backend_region=None,
        log_retention_duration=None,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        albfront_stack = AlbFrontStack(
            self,
            'albfront-stack',
            envname=envname,
            resource_prefix=resource_prefix,
            ecr_repository=ecr_repository,
            image_tag=image_tag,
            custom_domain=custom_domain,
            ip_ranges=ip_ranges,
            custom_auth=custom_auth,
            backend_region=backend_region,
            log_retention_duration=log_retention_duration,
        )

        Tags.of(albfront_stack).add('Application', f'{resource_prefix}-{envname}')

        Aspects.of(albfront_stack).add(AwsSolutionsChecks(reports=True, verbose=True))

        NagSuppressions.add_stack_suppressions(
            albfront_stack,
            suppressions=[
                NagPackSuppression(id=rule_suppressed['id'], reason=rule_suppressed['reason'])
                for rule_suppressed in ALBFRONT_STACK_CDK_NAG_EXCLUSIONS
            ],
            apply_to_nested_stacks=True,
        )
