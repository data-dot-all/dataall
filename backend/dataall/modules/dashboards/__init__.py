"""Contains the code related to dashboards"""
import logging
from typing import Set

from dataall.core.environment.services.environment_resource_manager import EnvironmentResourceManager
from dataall.modules.dashboards.db.dashboard_repository import DashboardRepository
from dataall.modules.dashboards.db.models import Dashboard
from dataall.modules.loader import ImportMode, ModuleInterface

log = logging.getLogger(__name__)


class DashboardApiModuleInterface(ModuleInterface):
    """Implements ModuleInterface for dashboard GraphQl lambda"""

    @staticmethod
    def is_supported(modes: Set[ImportMode]) -> bool:
        return ImportMode.API in modes

    def __init__(self):
        import dataall.modules.dashboards.api
        from dataall.api.Objects.Feed.registry import FeedRegistry, FeedDefinition
        from dataall.api.Objects.Glossary.registry import GlossaryRegistry, GlossaryDefinition
        from dataall.api.Objects.Vote.resolvers import add_vote_type
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

    def __init__(self):
        from dataall.modules.dashboards.indexers.dashboard_catalog_indexer import DashboardCatalogIndexer

        DashboardCatalogIndexer()
        log.info("Dashboard catalog indexer task has been loaded")
