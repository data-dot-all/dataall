import logging
import os
import sys

from dataall.core.catalog.catalog_indexer import CatalogIndexer
from dataall.db import get_engine, models
from dataall.modules.loader import load_modules, ImportMode
from dataall.searchproxy.indexers import DashboardIndexer
from dataall.utils.alarm_service import AlarmService

root = logging.getLogger()
root.setLevel(logging.INFO)
if not root.hasHandlers():
    root.addHandler(logging.StreamHandler(sys.stdout))
log = logging.getLogger(__name__)


def index_objects(engine):
    try:
        indexed_objects_counter = 0
        with engine.scoped_session() as session:
            for indexer in CatalogIndexer.all():
                indexed_objects_counter += indexer.index(session)

            all_dashboards: [models.Dashboard] = session.query(models.Dashboard).all()
            log.info(f'Found {len(all_dashboards)} dashboards')
            dashboard: models.Dashboard
            for dashboard in all_dashboards:
                DashboardIndexer.upsert(session=session, dashboard_uri=dashboard.dashboardUri)
                indexed_objects_counter = indexed_objects_counter + 1

            log.info(f'Successfully indexed {indexed_objects_counter} objects')
            return indexed_objects_counter
    except Exception as e:
        AlarmService().trigger_catalog_indexing_failure_alarm(error=str(e))
        raise e


if __name__ == '__main__':
    ENVNAME = os.environ.get('envname', 'local')
    ENGINE = get_engine(envname=ENVNAME)

    load_modules({ImportMode.CATALOG_INDEXER_TASK})
    index_objects(engine=ENGINE)
