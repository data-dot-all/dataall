"""Contains the code related to datasets"""
import logging
from typing import List, Type

from dataall.modules.dataset_sharing import SharingApiModuleInterface
from dataall.core.group.services.group_resource_manager import GroupResourceManager
from dataall.modules.datasets_base import DatasetBaseModuleInterface
from dataall.modules.datasets_base.db.models import DatasetTableColumn, DatasetStorageLocation, DatasetTable, Dataset
from dataall.modules.datasets.indexers.dataset_indexer import DatasetIndexer
from dataall.modules.datasets.indexers.location_indexer import DatasetLocationIndexer
from dataall.modules.datasets.indexers.table_indexer import DatasetTableIndexer
from dataall.modules.datasets.services.dataset_group_resource import DatasetGroupResource
from dataall.modules.datasets.services.permissions import GET_DATASET, UPDATE_DATASET
from dataall.modules.loader import ModuleInterface, ImportMode

log = logging.getLogger(__name__)


class DatasetApiModuleInterface(ModuleInterface):
    """Implements ModuleInterface for dataset GraphQl lambda"""

    @staticmethod
    def is_supported(modes):
        return ImportMode.API in modes

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        return [SharingApiModuleInterface, DatasetBaseModuleInterface]

    def __init__(self):
        # these imports are placed inside the method because they are only related to GraphQL api.
        from dataall.db.api import TargetType
        from dataall.api.Objects.Vote.resolvers import add_vote_type
        from dataall.api.Objects.Feed.registry import FeedRegistry, FeedDefinition
        from dataall.api.Objects.Glossary.registry import GlossaryRegistry, GlossaryDefinition

        import dataall.modules.datasets.api

        FeedRegistry.register(FeedDefinition("DatasetTableColumn", DatasetTableColumn))
        FeedRegistry.register(FeedDefinition("DatasetStorageLocation", DatasetStorageLocation))
        FeedRegistry.register(FeedDefinition("DatasetTable", DatasetTable))

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
            model=Dataset,
            reindexer=DatasetIndexer
        ))

        GlossaryRegistry.register(GlossaryDefinition(
            target_type="DatasetTable",
            object_type="DatasetTable",
            model=DatasetTable,
            reindexer=DatasetTableIndexer
        ))

        add_vote_type("dataset", DatasetIndexer)

        TargetType("dataset", GET_DATASET, UPDATE_DATASET)

        GroupResourceManager.register(DatasetGroupResource())

        log.info("API of datasets has been imported")


class DatasetAsyncHandlersModuleInterface(ModuleInterface):
    """Implements ModuleInterface for dataset async lambda"""

    @staticmethod
    def is_supported(modes: List[ImportMode]):
        return ImportMode.HANDLERS in modes

    def __init__(self):
        import dataall.modules.datasets.handlers
        log.info("Dataset handlers have been imported")


class DatasetCdkModuleInterface(ModuleInterface):
    """Loads dataset cdk stacks """

    @staticmethod
    def is_supported(modes: List[ImportMode]):
        return ImportMode.CDK in modes

    def __init__(self):
        import dataall.modules.datasets.cdk
        log.info("Dataset stacks have been imported")
