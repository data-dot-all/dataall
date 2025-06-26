from builtins import super

from aws_cdk import Stack
from .cloudfront import CloudfrontDistro
from .frontend_cognito_config import FrontendCognitoConfig


class CloudfrontStack(Stack):
    def __init__(
        self,
        scope,
        id,
        envname: str = 'dev',
        resource_prefix='dataall',
        tooling_account_id=None,
        custom_domain=None,
        custom_waf_rules=None,
        custom_auth=None,
        backend_region=None,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        distro = CloudfrontDistro(
            self,
            'CloudFront',
            envname=envname,
            resource_prefix=resource_prefix,
            tooling_account_id=tooling_account_id,
            custom_domain=custom_domain,
            custom_waf_rules=custom_waf_rules,
            backend_region=backend_region,
            **kwargs,
        )

        if not custom_auth:
            FrontendCognitoConfig(
                self,
                'FrontendCognitoConfig',
                envname=envname,
                resource_prefix=resource_prefix,
                custom_domain=custom_domain,
                backend_region=backend_region,
                execute_after=[distro],
                **kwargs,
            )
