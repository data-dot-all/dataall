import logging
import os

from dataall.base.aws.sts import SessionHelper
from dataall.base.aws.parameter_store import ParameterStoreManager
from dataall.base.db.exceptions import RequiredParameter
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService

log = logging.getLogger(__name__)


def update_group_permissions(context, source, input=None):
    return TenantPolicyService.update_group_permissions(
        data=input,
        check_perm=True,
    )


def list_tenant_permissions(context, source):
    return TenantPolicyService.list_tenant_permissions()


def list_tenant_groups(context, source, filter=None):
    return TenantPolicyService.list_tenant_groups(filter if filter else {})


def update_ssm_parameter(context, source, name: str = None, value: str = None):
    current_account = SessionHelper.get_account()
    region = os.getenv('AWS_REGION', 'eu-west-1')
    response = ParameterStoreManager.update_parameter(
        AwsAccountId=current_account,
        region=region,
        parameter_name=f'/dataall/{os.getenv("envname", "local")}/quicksightmonitoring/{name}',
        parameter_value=value,
    )
    return response
