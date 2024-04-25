"""Contains the code related to Maintenance Window Activity"""

import logging
from typing import Set

from dataall.base.loader import ImportMode, ModuleInterface

log = logging.getLogger(__name__)


class MaintenanceApiModuleInterface(ModuleInterface):
    """Implements ModuleInterface for Maintenance GraphQl lambda"""

    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        return ImportMode.API in modes

    def __init__(self):
        import dataall.modules.maintenance.api

        log.info('API of maintenance window activity has been imported')
