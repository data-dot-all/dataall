"""Contains the code related to datasets"""
import logging
from typing import List

from dataall.api.Objects.Feed.registry import FeedRegistry, FeedDefinition
from dataall.api.Objects.Glossary.registry import GlossaryRegistry, GlossaryDefinition
from dataall.modules.datasets.db.models import DatasetTableColumn, DatasetStorageLocation
from dataall.modules.loader import ModuleInterface, ImportMode
from dataall.searchproxy.indexers import upsert_folder

log = logging.getLogger(__name__)


class DatasetApiModuleInterface(ModuleInterface):
    """Implements ModuleInterface for dataset GraphQl lambda"""

    @classmethod
    def is_supported(cls, modes):
        return ImportMode.API in modes

    def __init__(self):
        import dataall.modules.datasets.api

        FeedRegistry.register(FeedDefinition("DatasetTableColumn", DatasetTableColumn))
        FeedRegistry.register(FeedDefinition("DatasetStorageLocation", DatasetStorageLocation))

        GlossaryRegistry.register(GlossaryDefinition("Column", "DatasetTableColumn", DatasetTableColumn))
        GlossaryRegistry.register(GlossaryDefinition(
            target_type="Folder",
            object_type="DatasetStorageLocation",
            model=DatasetStorageLocation,
            reindexer=upsert_folder
        ))

        log.info("API of datasets has been imported")


class DatasetAsyncHandlersModuleInterface(ModuleInterface):
    """Implements ModuleInterface for dataset async lambda"""

    @classmethod
    def is_supported(cls, modes: List[ImportMode]):
        return ImportMode.HANDLERS in modes

    def __init__(self):
        import dataall.modules.datasets.handlers
        log.info("Dataset handlers have been imported")


class DatasetCdkModuleInterface(ModuleInterface):
    """Loads dataset cdk stacks """

    @classmethod
    def is_supported(cls, modes: List[ImportMode]):
        return ImportMode.CDK in modes

    def __init__(self):
        import dataall.modules.datasets.cdk
        log.info("Dataset stacks have been imported")
