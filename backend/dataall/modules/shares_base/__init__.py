import logging
from typing import Set, List, Type
from dataall.base.loader import ModuleInterface, ImportMode

log = logging.getLogger(__name__)


class SharesBaseModuleInterface(ModuleInterface):
    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        supported_modes = {
            ImportMode.CDK,
            ImportMode.HANDLERS,
            ImportMode.STACK_UPDATER_TASK,
            ImportMode.CATALOG_INDEXER_TASK,
        }
        return modes & supported_modes

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        from dataall.modules.datasets_base import DatasetBaseModuleInterface

        return [DatasetBaseModuleInterface]

    def __init__(self):
        import dataall.modules.shares_base.services.shares_enums
        import dataall.modules.shares_base.services.share_permissions
        import dataall.modules.shares_base.services.sharing_service
        import dataall.modules.shares_base.handlers


class SharesBaseAPIModuleInterface(ModuleInterface):
    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        return ImportMode.API in modes

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        from dataall.modules.datasets_base import DatasetBaseApiModuleInterface

        return [DatasetBaseApiModuleInterface]

    def __init__(self):
        import dataall.modules.shares_base.services.shares_enums
        import dataall.modules.shares_base.services.share_permissions
        import dataall.modules.shares_base.services.sharing_service
        import dataall.modules.shares_base.handlers
        import dataall.modules.shares_base.api


class SharesBaseECSTaskModuleInterface(ModuleInterface):
    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        return ImportMode.SHARES_TASK in modes

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        from dataall.modules.datasets_base import DatasetBaseModuleInterface

        return [DatasetBaseModuleInterface]

    def __init__(self):
        import dataall.modules.shares_base.services.shares_enums
        import dataall.modules.shares_base.services.share_permissions
        import dataall.modules.shares_base.services.sharing_service

        log.info('Sharing ECS task has been imported')
