from typing import Set
from dataall.base.loader import ModuleInterface, ImportMode


class DatasetBaseModuleInterface(ModuleInterface):
    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        supported_modes = {
            ImportMode.CDK,
            ImportMode.HANDLERS,
            ImportMode.STACK_UPDATER_TASK,
            ImportMode.CATALOG_INDEXER_TASK,
            ImportMode.SHARES_TASK,
        }
        return modes & supported_modes

    def __init__(self):
        import dataall.modules.datasets_base.services.datasets_enums


class DatasetBaseApiModuleInterface(ModuleInterface):
    """Implements ModuleInterface for MLStudio GraphQl lambda"""

    @classmethod
    def is_supported(cls, modes):
        return ImportMode.API in modes

    def __init__(self):
        import dataall.modules.datasets_base.api
        import dataall.modules.datasets_base.services.datasets_enums
