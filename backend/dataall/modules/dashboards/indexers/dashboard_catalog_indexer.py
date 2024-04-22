import logging

from dataall.modules.catalog.indexers.catalog_indexer import CatalogIndexer
from dataall.modules.dashboards import Dashboard
from dataall.modules.dashboards.indexers.dashboard_indexer import DashboardIndexer

log = logging.getLogger(__name__)


class DashboardCatalogIndexer(CatalogIndexer):
    def index(self, session) -> int:
        all_dashboards: [Dashboard] = session.query(Dashboard).all()
        log.info(f'Found {len(all_dashboards)} dashboards')
        dashboard: Dashboard
        for dashboard in all_dashboards:
            DashboardIndexer.upsert(session=session, dashboard_uri=dashboard.dashboardUri)

        return len(all_dashboards)
