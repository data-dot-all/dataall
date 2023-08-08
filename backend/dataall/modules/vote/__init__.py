from typing import Set, List, Type

from dataall.base.loader import ModuleInterface, ImportMode
from dataall.modules.catalog import CatalogApiModuleInterface
from dataall.modules.vote import api


class VoteApiModuleInterface(ModuleInterface):

    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        return ImportMode.API in modes

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        return [CatalogApiModuleInterface]

    def __init__(self):
        import dataall.modules.vote.api
