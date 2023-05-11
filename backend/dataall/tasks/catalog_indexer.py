import logging
import os
import sys

from dataall.modules.datasets_base.db.dataset_repository import DatasetRepository
from dataall.modules.datasets_base.db.models import Dataset
from dataall.modules.datasets.indexers.location_indexer import DatasetLocationIndexer
from dataall.modules.datasets.indexers.table_indexer import DatasetTableIndexer
from dataall.db import get_engine, models
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

            all_datasets: [Dataset] = DatasetRepository.list_all_active_datasets(
                session
            )
            log.info(f'Found {len(all_datasets)} datasets')
            dataset: Dataset
            for dataset in all_datasets:
                tables = DatasetTableIndexer.upsert_all(session, dataset.datasetUri)
                folders = DatasetLocationIndexer.upsert_all(session, dataset_uri=dataset.datasetUri)
                indexed_objects_counter = (
                    indexed_objects_counter + len(tables) + len(folders) + 1
                )

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
    index_objects(engine=ENGINE)
