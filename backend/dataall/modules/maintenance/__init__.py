"""Contains the code related to Maintenance Window Activity"""

import logging
from typing import Set

from dataall.base.loader import ImportMode, ModuleInterface
from dataall.core.stacks.db.target_type_repositories import TargetType

log = logging.getLogger(__name__)


class MaintenanceApiModuleInterface(ModuleInterface):
    """Implements ModuleInterface for Maintenance GraphQl lambda"""

    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        return ImportMode.API in modes

    def __init__(self):
        import dataall.modules.maintenance.api

        # from dataall.modules.notebooks.services.notebook_permissions import GET_NOTEBOOK, UPDATE_NOTEBOOK
        #
        # TargetType('notebook', GET_NOTEBOOK, UPDATE_NOTEBOOK)
        print('API of maintenance window activity has been imported')
        log.info('API of maintenance window activity has been imported')

