import logging
import os
import sys
from abc import ABC
from typing import List

from dataall.db import get_engine
from dataall.modules.dashboards.db.models import Dashboard
from dataall.modules.loader import load_modules, ImportMode
from dataall.modules.dashboards.indexers.dashboard_indexer import DashboardIndexer
from dataall.utils.alarm_service import AlarmService

root = logging.getLogger()
root.setLevel(logging.INFO)
if not root.hasHandlers():
    root.addHandler(logging.StreamHandler(sys.stdout))
log = logging.getLogger(__name__)

load_modules({ImportMode.CATALOG_INDEXER_TASK})


class CatalogIndexer(ABC):
    def index(self, session) -> int:
        raise NotImplementedError("index is not implemented")


_indexers: List[CatalogIndexer] = []


def register_catalog_indexer(indexer: CatalogIndexer):
    _indexers.append(indexer)


def index_objects(engine):
    try:
        indexed_objects_counter = 0
        with engine.scoped_session() as session:
            for indexer in _indexers:
                indexed_objects_counter += indexer.index(session)

            all_dashboards: [Dashboard] = session.query(Dashboard).all()
            log.info(f'Found {len(all_dashboards)} dashboards')
            dashboard: Dashboard
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
    index_objects(engine=ENGINE)
