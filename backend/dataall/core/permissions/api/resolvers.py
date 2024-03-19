import logging
import os

from dataall.base.aws.sts import SessionHelper
from dataall.base.aws.parameter_store import ParameterStoreManager
from dataall.core.permissions.db.tenant.tenant_policy_repositories import TenantPolicy
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService

log = logging.getLogger(__name__)


def update_group_permissions(context, source, input=None):
    with context.engine.scoped_session() as session:
        return TenantPolicyService.update_group_permissions(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=input['groupUri'],
            data=input,
            check_perm=True,
        )


def list_tenant_permissions(context, source):
    with context.engine.scoped_session() as session:
        return TenantPolicyService.list_tenant_permissions(
            session=session, username=context.username, groups=context.groups
        )


def list_tenant_groups(context, source, filter=None):
    with context.engine.scoped_session() as session:
        return TenantPolicyService.list_tenant_groups(
            session=session, username=context.username, groups=context.groups, data=filter if filter else {}
        )


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
