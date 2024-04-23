import logging

from dataall.base.api.context import Context
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyValidationService
from dataall.core.stacks.api import stack_helper
from dataall.base.db import exceptions
from dataall.modules.maintenance.api.enums import MaintenanceModes
from dataall.modules.maintenance.api.types import Maintenance
from dataall.modules.maintenance.services.maintenance_service import MaintenanceService
from dataall.modules.notebooks.api.enums import SagemakerNotebookRole
from dataall.modules.notebooks.db.notebook_models import SagemakerNotebook
from dataall.modules.notebooks.services.notebook_service import NotebookService, NotebookCreationRequest


def start_maintenance_window(context: Context, source: Maintenance, mode: str):
    """Starts the maintenance window"""
    if mode not in [item.value for item in list(MaintenanceModes)]:
        raise Exception('Mode is not conforming to the MaintenanceModes enums')
    # Check from the context if the groups contains the DataAdminstrators group
    logging.info(context.groups)
    if not TenantPolicyValidationService.is_tenant_admin(context.groups):
        raise Exception('Only data.all admin group members can start maintenance window')
    return MaintenanceService.start_maintenance_window(engine=context.engine, mode=mode)


def stop_maintenance_window(context: Context, source: Maintenance):
    # Check from the context if the groups contains the DataAdminstrators group
    if not TenantPolicyValidationService.is_tenant_admin(context.groups):
        raise Exception('Only data.all admin group members can stop maintenance window')
    return MaintenanceService.stop_maintenance_window(engine=context.engine)

def get_maintenance_window_status(context: Context, source: Maintenance):
    return MaintenanceService.get_maintenance_window_status(engine=context.engine)

def get_maintenance_window_mode(context: Context, source: Maintenance):
    return MaintenanceService.get_maintenance_window_mode()
