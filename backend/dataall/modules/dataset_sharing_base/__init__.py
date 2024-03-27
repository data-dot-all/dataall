from typing import Set, List, Type
from dataall.base.loader import ModuleInterface, ImportMode
class DatasetSharingBaseModuleInterface(ModuleInterface):

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        from dataall.modules.datasets_base import DatasetBaseModuleInterface
        return [DatasetBaseModuleInterface]

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
        import dataall.modules.dataset_sharing_base.api
