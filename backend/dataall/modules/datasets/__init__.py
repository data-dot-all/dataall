"""Contains the code related to datasets"""
import logging
from typing import List, Type, Set

from dataall.base.loader import ModuleInterface, ImportMode

log = logging.getLogger(__name__)


class DatasetApiModuleInterface(ModuleInterface):
    """Implements ModuleInterface for dataset GraphQl lambda"""

    @staticmethod
    def is_supported(modes):
        return ImportMode.API in modes

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        from dataall.modules.datasets_base import DatasetBaseModuleInterface
        from dataall.modules.dataset_sharing import SharingApiModuleInterface
        from dataall.modules.catalog import CatalogApiModuleInterface
        from dataall.modules.feed import FeedApiModuleInterface
        from dataall.modules.vote import VoteApiModuleInterface

        return [
            SharingApiModuleInterface, DatasetBaseModuleInterface, CatalogApiModuleInterface,
            FeedApiModuleInterface, VoteApiModuleInterface
        ]

    def __init__(self):
        # these imports are placed inside the method because they are only related to GraphQL api.
        from dataall.core.stacks.db.target_type_repositories import TargetType
        from dataall.modules.vote.api.resolvers import add_vote_type
        from dataall.modules.feed.api.registry import FeedRegistry, FeedDefinition
        from dataall.modules.catalog.api.registry import GlossaryRegistry, GlossaryDefinition
        from dataall.core.environment.services.environment_resource_manager import EnvironmentResourceManager
        from dataall.modules.datasets.indexers.dataset_indexer import DatasetIndexer
        from dataall.modules.datasets.indexers.location_indexer import DatasetLocationIndexer
        from dataall.modules.datasets.indexers.table_indexer import DatasetTableIndexer

        import dataall.modules.datasets.api
        from dataall.modules.datasets.services.dataset_permissions import GET_DATASET, UPDATE_DATASET
        from dataall.modules.datasets_base.db.dataset_repositories import DatasetRepository
        from dataall.modules.datasets_base.db.dataset_models import DatasetStorageLocation, DatasetTable, Dataset

        FeedRegistry.register(FeedDefinition("DatasetStorageLocation", DatasetStorageLocation))
        FeedRegistry.register(FeedDefinition("DatasetTable", DatasetTable))
        FeedRegistry.register(FeedDefinition("Dataset", Dataset))

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

        EnvironmentResourceManager.register(DatasetRepository())

        log.info("API of datasets has been imported")


class DatasetAsyncHandlersModuleInterface(ModuleInterface):
    """Implements ModuleInterface for dataset async lambda"""

    @staticmethod
    def is_supported(modes: Set[ImportMode]):
        return ImportMode.HANDLERS in modes

    def __init__(self):
        import dataall.modules.datasets.handlers
        log.info("Dataset handlers have been imported")

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        from dataall.modules.datasets_base import DatasetBaseModuleInterface
        from dataall.modules.dataset_sharing import SharingAsyncHandlersModuleInterface

        return [SharingAsyncHandlersModuleInterface, DatasetBaseModuleInterface]


class DatasetCdkModuleInterface(ModuleInterface):
    """Loads dataset cdk stacks """

    @staticmethod
    def is_supported(modes: Set[ImportMode]):
        return ImportMode.CDK in modes

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        from dataall.modules.datasets_base import DatasetBaseModuleInterface
        from dataall.modules.dataset_sharing import DataSharingCdkModuleInterface
        return [DatasetBaseModuleInterface, DataSharingCdkModuleInterface]

    def __init__(self):
        import dataall.modules.datasets.cdk
        from dataall.core.environment.cdk.environment_stack import EnvironmentSetup
        from dataall.modules.datasets.cdk.dataset_glue_profiler_extension import DatasetGlueProfilerExtension
        from dataall.modules.datasets.cdk.dataset_custom_resources_extension import DatasetCustomResourcesExtension

        EnvironmentSetup.register(DatasetGlueProfilerExtension)
        EnvironmentSetup.register(DatasetCustomResourcesExtension)

        log.info("Dataset stacks have been imported")


class DatasetStackUpdaterModuleInterface(ModuleInterface):

    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        return ImportMode.STACK_UPDATER_TASK in modes

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        from dataall.modules.datasets_base import DatasetBaseModuleInterface

        return [DatasetBaseModuleInterface]

    def __init__(self):
        from dataall.modules.datasets.tasks.dataset_stack_finder import DatasetStackFinder

        DatasetStackFinder()
        log.info("Dataset stack updater task has been loaded")


class DatasetCatalogIndexerModuleInterface(ModuleInterface):

    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        return ImportMode.CATALOG_INDEXER_TASK in modes

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        from dataall.modules.datasets_base import DatasetBaseModuleInterface
        from dataall.modules.catalog import CatalogIndexerModuleInterface

        return [DatasetBaseModuleInterface, CatalogIndexerModuleInterface]

    def __init__(self):
        from dataall.modules.datasets.indexers.dataset_catalog_indexer import DatasetCatalogIndexer

        DatasetCatalogIndexer()
        log.info("Dataset catalog indexer task has been loaded")
