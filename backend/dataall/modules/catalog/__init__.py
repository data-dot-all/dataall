from typing import Set

from dataall.base.loader import ModuleInterface, ImportMode


class CatalogIndexerModuleInterface(ModuleInterface):
    """
    Base code that can be imported with all modes
    """

    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        return ImportMode.CATALOG_INDEXER_TASK in modes

    def __init__(self):
        from dataall.modules.catalog import tasks


class CatalogAsyncHandlersModuleInterface(ModuleInterface):
    """Implements ModuleInterface for catalog async lambda"""

    @staticmethod
    def is_supported(modes: Set[ImportMode]):
        return ImportMode.HANDLERS in modes

    def __init__(self):
        import dataall.modules.catalog.handlers


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
