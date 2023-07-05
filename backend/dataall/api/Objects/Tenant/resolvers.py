import os

from dataall.aws.handlers.sts import SessionHelper
from dataall.aws.handlers.parameter_store import ParameterStoreManager
from dataall.core.permissions.db.tenant_policy import TenantPolicy


def update_group_permissions(context, source, input=None):
    with context.engine.scoped_session() as session:
        return TenantPolicy.update_group_permissions(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=input['groupUri'],
            data=input,
            check_perm=True,
        )


def list_tenant_permissions(context, source):
    with context.engine.scoped_session() as session:
        return TenantPolicy.list_tenant_permissions(
            session=session, username=context.username, groups=context.groups
        )


def list_tenant_groups(context, source, filter=None):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return TenantPolicy.list_tenant_groups(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=None,
            data=filter,
            check_perm=True,
        )


def update_ssm_parameter(context, source, name: str = None, value: str = None):
    current_account = SessionHelper.get_account()
    region = os.getenv('AWS_REGION', 'eu-west-1')
    print(value)
    print(name)
    response = ParameterStoreManager.update_parameter(AwsAccountId=current_account, region=region, parameter_name=f'/dataall/{os.getenv("envname", "local")}/quicksightmonitoring/{name}', parameter_value=value)
    return response
