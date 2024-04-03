from typing import Set
from dataall.base.loader import ModuleInterface, ImportMode


class DatasetBaseModuleInterface(ModuleInterface):
    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        supported_modes = {
            ImportMode.API,
            ImportMode.CDK,
            ImportMode.HANDLERS,
            ImportMode.STACK_UPDATER_TASK,
            ImportMode.CATALOG_INDEXER_TASK,
        }
        return modes & supported_modes
