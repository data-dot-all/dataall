from typing import Set, List, Type

from dataall.base.loader import ModuleInterface, ImportMode


class VoteApiModuleInterface(ModuleInterface):
    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        return ImportMode.API in modes

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        from dataall.modules.catalog import CatalogApiModuleInterface

        return [CatalogApiModuleInterface]

    def __init__(self):
        import dataall.modules.vote.api
