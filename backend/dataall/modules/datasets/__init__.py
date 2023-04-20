"""Contains the code related to datasets"""
import logging
from typing import List

from dataall.db import models
from dataall.modules.datasets.db.models import DatasetTableColumn, DatasetStorageLocation
from dataall.modules.datasets.indexers.dataset_indexer import DatasetIndexer
from dataall.modules.datasets.indexers.location_indexer import DatasetLocationIndexer
from dataall.modules.datasets.indexers.table_indexer import DatasetTableIndexer
from dataall.modules.loader import ModuleInterface, ImportMode

log = logging.getLogger(__name__)


class DatasetApiModuleInterface(ModuleInterface):
    """Implements ModuleInterface for dataset GraphQl lambda"""

    @classmethod
    def is_supported(cls, modes):
        return ImportMode.API in modes

    def __init__(self):
        from dataall.api.Objects.Feed.registry import FeedRegistry, FeedDefinition
        from dataall.api.Objects.Glossary.registry import GlossaryRegistry, GlossaryDefinition

        import dataall.modules.datasets.api

        FeedRegistry.register(FeedDefinition("DatasetTableColumn", DatasetTableColumn))
        FeedRegistry.register(FeedDefinition("DatasetStorageLocation", DatasetStorageLocation))

        GlossaryRegistry.register(GlossaryDefinition("Column", "DatasetTableColumn", DatasetTableColumn))
        GlossaryRegistry.register(GlossaryDefinition(
            target_type="Folder",
            object_type="DatasetStorageLocation",
            model=DatasetStorageLocation,
            reindexer=DatasetLocationIndexer
        ))

        GlossaryRegistry.register(GlossaryDefinition(
            target_type="Dataset",
            object_type="Dataset",
            model=models.Dataset,
            reindexer=DatasetIndexer
        ))

        GlossaryRegistry.register(GlossaryDefinition(
            target_type="DatasetTable",
            object_type="DatasetTable",
            model=models.DatasetTable,
            reindexer=DatasetTableIndexer
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
