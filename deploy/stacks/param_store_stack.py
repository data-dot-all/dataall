import random
import string

import boto3
from aws_cdk import (
    aws_ssm,
    SecretValue
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
        enable_pivot_role_auto_create=False,
        pivot_role_name='dataallPivotRole',
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

        aws_ssm.StringParameter(
            self,
            f'dataallCreationPivotRole{envname}',
            parameter_name=f"/dataall/{envname}/pivotRole/enablePivotRoleAutoCreate",
            string_value=str(enable_pivot_role_auto_create),
        )

        aws_ssm.StringParameter(
            self,
            f'dataallPivotRoleName{envname}',
            parameter_name=f"/dataall/{envname}/pivotRole/pivotRoleName",
            string_value=str(pivot_role_name),
            description=f"Stores dataall pivot role name for environment {envname}",
        )

        existing_external_id = _get_external_id_value(envname=envname, account_id=self.account, region=self.region)
        external_id_value = existing_external_id if existing_external_id else _generate_external_id()

        aws_ssm.StringParameter(
            self,
            f'dataallExternalId{envname}',
            parameter_name=f"/dataall/{envname}/pivotRole/externalId",
            string_value=str(external_id_value),
            description=f"Stores dataall external id for environment {envname}",
        )

def _get_external_id_value(envname, account_id, region):
    """For first deployments it returns False,
    for existing deployments it returns the ssm parameter value generated in the first deployment
    for prior to V1.5.1 upgrades it returns the secret from secrets manager
    """
    cdk_look_up_role = 'arn:aws:iam::{}:role/cdk-hnb659fds-lookup-role-{}-{}'.format(account_id, account_id, region)
    base_session = boto3.Session()
    assume_role_dict = dict(
        RoleArn=cdk_look_up_role,
        RoleSessionName=cdk_look_up_role.split('/')[1],
    )
    sts = base_session.client(
        'sts',
        region_name=region,
        endpoint_url=f"https://sts.{region}.amazonaws.com"
    )
    parameter_path = f"/dataall/{envname}/pivotRole/externalId"

    try:
        response = sts.assume_role(**assume_role_dict)
        session = boto3.Session(
            aws_access_key_id=response['Credentials']['AccessKeyId'],
            aws_secret_access_key=response['Credentials']['SecretAccessKey'],
            aws_session_token=response['Credentials']['SessionToken'],
        )
        ssm_client = session.client('ssm', region_name=region)
        parameter_value = ssm_client.get_parameter(Name=parameter_path)['Parameter']['Value']
        return parameter_value
    except:
        return False


def _generate_external_id():
    allowed_chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return ''.join(random.choice(allowed_chars) for i in range(32))