from aws_cdk import Stage, Tags, Aspects
from cdk_nag import NagSuppressions, AwsSolutionsChecks, NagPackSuppression

from .cdk_nag_exclusions import CLOUDFRONT_STACK_CDK_NAG_EXCLUSIONS
from .cloudfront_stack import CloudfrontStack


class CloudfrontStage(Stage):
    def __init__(
        self,
        scope,
        id: str,
        envname='dev',
        resource_prefix='dataall',
        tooling_account_id=None,
        custom_domain=None,
        custom_waf_rules=None,
        custom_auth=None,
        backend_region=None,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        cloudfront_stack = CloudfrontStack(
            self,
            'cloudfront-stack',
            envname=envname,
            resource_prefix=resource_prefix,
            tooling_account_id=tooling_account_id,
            custom_domain=custom_domain,
            custom_waf_rules=custom_waf_rules,
            custom_auth=custom_auth,
            backend_region=backend_region,
        )

        Tags.of(cloudfront_stack).add('Application', f'{resource_prefix}-{envname}')

        Aspects.of(cloudfront_stack).add(AwsSolutionsChecks(reports=True, verbose=True))

        NagSuppressions.add_stack_suppressions(
            cloudfront_stack,
            suppressions=[
                NagPackSuppression(id=rule_suppressed['id'], reason=rule_suppressed['reason'])
                for rule_suppressed in CLOUDFRONT_STACK_CDK_NAG_EXCLUSIONS
            ],
            apply_to_nested_stacks=True,
        )
