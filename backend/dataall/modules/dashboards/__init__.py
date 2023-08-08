"""Contains the code related to dashboards"""
import logging
from typing import Set, List, Type

from dataall.core.environment.services.environment_resource_manager import EnvironmentResourceManager
from dataall.modules.catalog import CatalogApiModuleInterface
from dataall.modules.dashboards.db.dashboard_repository import DashboardRepository
from dataall.modules.dashboards.db.models import Dashboard
from dataall.base.loader import ImportMode, ModuleInterface
from dataall.modules.feed import FeedApiModuleInterface
from dataall.modules.vote import VoteApiModuleInterface

log = logging.getLogger(__name__)


class DashboardApiModuleInterface(ModuleInterface):
    """Implements ModuleInterface for dashboard GraphQl lambda"""

    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        return ImportMode.API in modes

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        return [FeedApiModuleInterface, CatalogApiModuleInterface, VoteApiModuleInterface]

    def __init__(self):
        import dataall.modules.dashboards.api
        from dataall.modules.feed.api.registry import FeedRegistry, FeedDefinition
        from dataall.modules.catalog.api.registry import GlossaryRegistry, GlossaryDefinition
        from dataall.modules.vote.api.resolvers import add_vote_type
        from dataall.modules.dashboards.indexers.dashboard_indexer import DashboardIndexer

        FeedRegistry.register(FeedDefinition("Dashboard", Dashboard))

        GlossaryRegistry.register(GlossaryDefinition(
            target_type="Dashboard",
            object_type="Dashboard",
            model=Dashboard,
            reindexer=DashboardIndexer
        ))

        add_vote_type("dashboard", DashboardIndexer)

        EnvironmentResourceManager.register(DashboardRepository())
        log.info("Dashboard API has been loaded")


class DashboardCdkModuleInterface(ModuleInterface):

    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        return ImportMode.CDK in modes

    def __init__(self):
        import dataall.modules.dashboards.cdk
        log.info("Dashboard CDK code has been loaded")


class DashboardCatalogIndexerModuleInterface(ModuleInterface):

    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        return ImportMode.CATALOG_INDEXER_TASK in modes

    @staticmethod
    def depends_on() -> List[Type['ModuleInterface']]:
        return [CatalogApiModuleInterface]

    def __init__(self):
        from dataall.modules.dashboards.indexers.dashboard_catalog_indexer import DashboardCatalogIndexer

        DashboardCatalogIndexer()
        log.info("Dashboard catalog indexer task has been loaded")
