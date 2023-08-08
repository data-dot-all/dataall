from typing import Set, List, Type

from dataall.base.loader import ModuleInterface, ImportMode


class DatasetBaseModuleInterface(ModuleInterface):
    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        return True
