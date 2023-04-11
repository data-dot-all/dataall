"""Contains the code related to datasets"""
import logging
from typing import List

from dataall.core.utils.model_registry import ModelDefinition, FeedRegistry, GlossaryRegistry
from dataall.modules.datasets.db.table_column_model import DatasetTableColumn
from dataall.modules.loader import ModuleInterface, ImportMode

log = logging.getLogger(__name__)


class DatasetApiModuleInterface(ModuleInterface):
    """Implements ModuleInterface for dataset GraphQl lambda"""

    @classmethod
    def is_supported(cls, modes):
        return ImportMode.API in modes

    def __init__(self):
        import dataall.modules.datasets.api
        FeedRegistry.register(ModelDefinition("DatasetTableColumn", DatasetTableColumn))
        GlossaryRegistry.register(ModelDefinition("DatasetTableColumn", DatasetTableColumn))
        log.info("API of datasets has been imported")


class DatasetAsyncHandlersModuleInterface(ModuleInterface):
    """Implements ModuleInterface for dataset async lambda"""

    @classmethod
    def is_supported(cls, modes: List[ImportMode]):
        return ImportMode.HANDLERS in modes

    def __init__(self):
        import dataall.modules.datasets.handlers
        log.info("Dataset handlers have been imported")
