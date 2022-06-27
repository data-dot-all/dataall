from builtins import super

from aws_cdk import Stack
from .cloudfront import CloudfrontDistro
from .auth_at_edge import AuthAtEdge


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
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        auth_at_edge = AuthAtEdge(
            self,
            f'AuthAtEdge',
            envname=envname,
            resource_prefix=resource_prefix,
            **kwargs,
        )

        distro = CloudfrontDistro(
            self,
            f'CloudFront',
            envname=envname,
            resource_prefix=resource_prefix,
            auth_at_edge=auth_at_edge,
            tooling_account_id=tooling_account_id,
            custom_domain=custom_domain,
            custom_waf_rules=custom_waf_rules,
            **kwargs,
        )
