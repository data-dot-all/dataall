import logging
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService, TenantActionsService

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
    return TenantActionsService.update_monitoring_ssm_parameter(name, value)
