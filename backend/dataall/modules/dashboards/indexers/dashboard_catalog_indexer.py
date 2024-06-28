import logging

from typing import List

from dataall.modules.catalog.indexers.catalog_indexer import CatalogIndexer
from dataall.modules.dashboards.db.dashboard_models import Dashboard
from dataall.modules.dashboards.indexers.dashboard_indexer import DashboardIndexer

log = logging.getLogger(__name__)


class DashboardCatalogIndexer(CatalogIndexer):
    def index(self, session) -> List[str]:
        all_dashboards: List[Dashboard] = session.query(Dashboard).all()
        all_dashboard_uris = []

        log.info(f'Found {len(all_dashboards)} dashboards')
        dashboard: Dashboard
        for dashboard in all_dashboards:
            all_dashboard_uris.append(dashboard.dashboardUri)
            DashboardIndexer.upsert(session=session, dashboard_uri=dashboard.dashboardUri)

        return all_dashboard_uris
