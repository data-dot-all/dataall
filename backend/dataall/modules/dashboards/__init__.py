"""Contains the code related to dashboards"""
import logging

from dataall.modules.dashboards.db.models import Dashboard
from dataall.modules.loader import ImportMode, ModuleInterface

log = logging.getLogger(__name__)


class DashboardApiModuleInterface(ModuleInterface):
    """Implements ModuleInterface for dashboard GraphQl lambda"""

    @staticmethod
    def is_supported(modes):
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

