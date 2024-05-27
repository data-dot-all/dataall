import logging
from typing import Set
from dataall.base.loader import ModuleInterface, ImportMode

log = logging.getLogger(__name__)


class SharesBaseModuleInterface(ModuleInterface):
    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        supported_modes = {
            ImportMode.API,
            ImportMode.CDK,
            ImportMode.STACK_UPDATER_TASK,
            ImportMode.CATALOG_INDEXER_TASK,
        }
        return modes & supported_modes

    def __init__(self):
        import dataall.modules.shares_base.services.shares_enums
        import dataall.modules.shares_base.services.share_permissions
        import dataall.modules.shares_base.services.sharing_service
        import dataall.modules.shares_base.handlers


class SharesBaseAsyncModuleInterface(ModuleInterface):
    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        return ImportMode.HANDLERS in modes

    def __init__(self):
        import dataall.modules.shares_base.handlers

        log.info('Sharing handlers have been imported')
