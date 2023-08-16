from typing import Set

from dataall.base.loader import ModuleInterface, ImportMode
from dataall.modules.catalog import tasks


class CatalogApiModuleInterface(ModuleInterface):
    """
    Implements ModuleInterface for catalog code in GraphQl lambda.
    This module interface is used in dashboards and datasets

    """

    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        return ImportMode.API in modes

    def __init__(self):
        import dataall.modules.catalog.api
        import dataall.modules.catalog.indexers
