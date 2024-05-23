from dataall.base.api.context import Context
from dataall.modules.maintenance.api.enums import MaintenanceModes
from dataall.modules.maintenance.api.types import Maintenance
from dataall.modules.maintenance.services.maintenance_service import MaintenanceService


def start_maintenance_window(context: Context, source: Maintenance, mode: str):
    if mode not in [item.value for item in list(MaintenanceModes)]:
        raise Exception('Mode is not conforming to the MaintenanceModes enum')
    return MaintenanceService.start_maintenance_window(mode=mode)


def stop_maintenance_window(context: Context, source: Maintenance):
    return MaintenanceService.stop_maintenance_window()


def get_maintenance_window_status(context: Context, source: Maintenance):
    return MaintenanceService.get_maintenance_window_status()
