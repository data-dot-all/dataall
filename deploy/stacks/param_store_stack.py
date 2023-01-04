from aws_cdk import (
    aws_ssm,
)

from .pyNestedStack import pyNestedClass


class ParamStoreStack(pyNestedClass):
    def __init__(
        self,
        scope,
        id,
        envname='dev',
        resource_prefix='dataall',
        custom_domain=None,
        enable_cw_canaries=False,
        quicksight_enabled=False,
        shared_dashboard_sessions='anonymous',
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        self.resource_prefix_param = aws_ssm.StringParameter(
            self,
            f'ResourcePrefixParam{envname}',
            parameter_name=f'/dataall/{envname}/resourcePrefix',
            string_value=resource_prefix,
        )

        if custom_domain:
            custom_domain = custom_domain['hosted_zone_name']
            frontend_alternate_domain = custom_domain
            userguide_alternate_domain = 'userguide.' + custom_domain

            aws_ssm.StringParameter(
                self,
                f'FrontendCustomDomain{envname}',
                parameter_name=f'/dataall/{envname}/frontend/custom_domain_name',
                string_value=frontend_alternate_domain,
            )

            aws_ssm.StringParameter(
                self,
                f'UserGuideCustomDomain{envname}',
                parameter_name=f'/dataall/{envname}/userguide/custom_domain_name',
                string_value=userguide_alternate_domain,
            )

        if enable_cw_canaries:
            aws_ssm.StringParameter(
                self,
                f'CWCanariesEnv{envname}',
                parameter_name=f'/dataall/{envname}/canary/environment_account',
                string_value='updateme(e.g: 1234xxxx)',
            )
            aws_ssm.StringParameter(
                self,
                f'CWCanariesRegion{envname}',
                parameter_name=f'/dataall/{envname}/canary/environment_region',
                string_value='updateme(e.g: eu-west-1)',
            )

        if quicksight_enabled:
            aws_ssm.StringParameter(
                self,
                f'QSVPCConnectionIdEnv{envname}',
                parameter_name=f'/dataall/{envname}/quicksightmonitoring/VPCConnectionId',
                string_value='updateme',
            )
            aws_ssm.StringParameter(
                self,
                f'QSDashboardIdEnv{envname}',
                parameter_name=f'/dataall/{envname}/quicksightmonitoring/DashboardId',
                string_value='updateme',
            )

        aws_ssm.StringParameter(
            self,
            f'dataallQuicksightConfiguration{envname}',
            parameter_name=f"/dataall/{envname}/quicksight/sharedDashboardsSessions",
            string_value=shared_dashboard_sessions,
        )