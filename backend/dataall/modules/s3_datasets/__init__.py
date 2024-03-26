"""Contains the code related to datasets"""

import logging
from typing import List, Type, Set

from dataall.base.loader import ModuleInterface, ImportMode

log = logging.getLogger(__name__)


class S3DatasetApiModuleInterface(ModuleInterface):
    """Implements ModuleInterface for dataset GraphQl lambda"""

    @staticmethod
    def is_supported(modes):
        return ImportMode.API in modes

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        from dataall.modules.datasets_base import DatasetBaseModuleInterface
        from dataall.modules.dataset_sharing_base import DatasetSharingBaseModuleInterface
        from dataall.modules.catalog import CatalogApiModuleInterface
        from dataall.modules.feed import FeedApiModuleInterface
        from dataall.modules.vote import VoteApiModuleInterface

        return [
            DatasetSharingBaseModuleInterface,
            DatasetBaseModuleInterface,
            CatalogApiModuleInterface,
            FeedApiModuleInterface,
            VoteApiModuleInterface,
        ]

    def __init__(self):
        # these imports are placed inside the method because they are only related to GraphQL api.
        from dataall.core.stacks.db.target_type_repositories import TargetType
        from dataall.modules.vote.services.vote_service import add_vote_type
        from dataall.modules.feed.api.registry import FeedRegistry, FeedDefinition
        from dataall.modules.catalog.indexers.registry import GlossaryRegistry, GlossaryDefinition
        from dataall.core.environment.services.environment_resource_manager import EnvironmentResourceManager
        from dataall.modules.s3_datasets.indexers.dataset_indexer import DatasetIndexer
        from dataall.modules.s3_datasets.indexers.location_indexer import DatasetLocationIndexer
        from dataall.modules.s3_datasets.indexers.table_indexer import DatasetTableIndexer

        import dataall.modules.s3_datasets.api
        #from dataall.modules.s3_datasets.services.dataset_permissions import GET_DATASET, UPDATE_DATASET ##TODO
        from dataall.modules.datasets_base.db.dataset_base_repositories import DatasetBaseRepository
        from dataall.modules.datasets_base.db.dataset_base_models import Dataset
        from dataall.modules.s3_datasets.db.dataset_models import S3Dataset, DatasetTable, DatasetStorageLocation


        FeedRegistry.register(FeedDefinition('DatasetStorageLocation', DatasetStorageLocation))
        FeedRegistry.register(FeedDefinition('DatasetTable', DatasetTable))
        #FeedRegistry.register(FeedDefinition('Dataset', Dataset))

        GlossaryRegistry.register(
            GlossaryDefinition(
                target_type='Folder',
                object_type='DatasetStorageLocation',
                model=DatasetStorageLocation,
                reindexer=DatasetLocationIndexer,
            )
        )

        # GlossaryRegistry.register(
        #     GlossaryDefinition(target_type='Dataset', object_type='Dataset', model=Dataset, reindexer=DatasetIndexer)
        # ) ##TODO

        GlossaryRegistry.register(
            GlossaryDefinition(
                target_type='DatasetTable',
                object_type='DatasetTable',
                model=DatasetTable,
                reindexer=DatasetTableIndexer,
            )
        )

        ## add_vote_type('dataset', DatasetIndexer) ##TODO

        #TargetType('dataset', GET_DATASET, UPDATE_DATASET) ##TODO

        ## EnvironmentResourceManager.register(DatasetRepository()) ##TODO

        log.info('API of datasets has been imported')


class S3DatasetAsyncHandlersModuleInterface(ModuleInterface):
    """Implements ModuleInterface for dataset async lambda"""

    @staticmethod
    def is_supported(modes: Set[ImportMode]):
        return ImportMode.HANDLERS in modes

    def __init__(self):
        import dataall.modules.s3_datasets.handlers

        log.info('Dataset handlers have been imported')

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        from dataall.modules.datasets_base import DatasetBaseModuleInterface
        from dataall.modules.dataset_sharing_base import DatasetSharingBaseModuleInterface

        return [DatasetBaseModuleInterface, DatasetSharingBaseModuleInterface]


class S3DatasetCdkModuleInterface(ModuleInterface):
    """Loads dataset cdk stacks"""

    @staticmethod
    def is_supported(modes: Set[ImportMode]):
        return ImportMode.CDK in modes

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        from dataall.modules.datasets_base import DatasetBaseModuleInterface
        from dataall.modules.dataset_sharing_base import DatasetSharingBaseModuleInterface

        return [DatasetBaseModuleInterface, DatasetSharingBaseModuleInterface]

    def __init__(self):
        import dataall.modules.s3_datasets.cdk
        from dataall.core.environment.cdk.environment_stack import EnvironmentSetup
        from dataall.modules.s3_datasets.cdk.dataset_glue_profiler_extension import DatasetGlueProfilerExtension
        from dataall.modules.s3_datasets.cdk.dataset_custom_resources_extension import DatasetCustomResourcesExtension

        EnvironmentSetup.register(DatasetGlueProfilerExtension)
        EnvironmentSetup.register(DatasetCustomResourcesExtension)

        log.info('Dataset stacks have been imported')


class S3DatasetStackUpdaterModuleInterface(ModuleInterface):
    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        return ImportMode.STACK_UPDATER_TASK in modes

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        from dataall.modules.datasets_base import DatasetBaseModuleInterface

        return [DatasetBaseModuleInterface]

    def __init__(self):
        from dataall.modules.s3_datasets.tasks.dataset_stack_finder import DatasetStackFinder

        DatasetStackFinder()
        log.info('Dataset stack updater task has been loaded')


class S3DatasetCatalogIndexerModuleInterface(ModuleInterface):
    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        return ImportMode.CATALOG_INDEXER_TASK in modes

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        from dataall.modules.datasets_base import DatasetBaseModuleInterface
        from dataall.modules.catalog import CatalogIndexerModuleInterface

        return [DatasetBaseModuleInterface, CatalogIndexerModuleInterface]

    def __init__(self):
        from dataall.modules.s3_datasets.indexers.dataset_catalog_indexer import DatasetCatalogIndexer

        DatasetCatalogIndexer()
        log.info('Dataset catalog indexer task has been loaded')
