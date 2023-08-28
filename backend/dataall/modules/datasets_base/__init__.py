from typing import Set
from dataall.base.loader import ModuleInterface, ImportMode


class DatasetBaseModuleInterface(ModuleInterface):
    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        return True
    # def is_supported(modes: Set[ImportMode]) -> bool:
    #     supported_modes = [
    #         ImportMode.API,
    #         ImportMode.CDK,
    #         ImportMode.HANDLERS,
    #         ImportMode.STACK_UPDATER_TASK,
    #         ImportMode.CATALOG_INDEXER_TASK
    #     ]
    #     supported = [x in supported_modes for x in modes]
    #     return True in supported

