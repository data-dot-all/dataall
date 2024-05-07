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

    def __init__(self):
        import dataall.modules.datasets_base.api
