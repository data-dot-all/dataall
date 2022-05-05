import logging
import os
import sys

from .. import db
from ..db import get_engine, exceptions
from ..db import models
from ..searchproxy import indexers
from ..searchproxy.connect import (
    connect,
)
from ..utils.alarm_service import AlarmService

root = logging.getLogger()
root.setLevel(logging.INFO)
if not root.hasHandlers():
    root.addHandler(logging.StreamHandler(sys.stdout))
log = logging.getLogger(__name__)


def index_objects(engine, es):
    try:
        if not es:
            raise exceptions.AWSResourceNotFound(action="CATALOG_INDEXER_TASK", message="ES configuration not found")
        indexed_objects_counter = 0
        with engine.scoped_session() as session:

            all_datasets: [models.Dataset] = db.api.Dataset.list_all_active_datasets(session)
            log.info(f"Found {len(all_datasets)} datasets")
            dataset: models.Dataset
            for dataset in all_datasets:
                tables = indexers.upsert_dataset_tables(session, es, dataset.datasetUri)
                folders = indexers.upsert_dataset_folders(session, es, dataset.datasetUri)
                indexed_objects_counter = indexed_objects_counter + len(tables) + len(folders) + 1

            all_dashboards: [models.Dashboard] = session.query(models.Dashboard).all()
            log.info(f"Found {len(all_dashboards)} dashboards")
            dashboard: models.Dashboard
            for dashboard in all_dashboards:
                indexers.upsert_dashboard(session, es, dashboard.dashboardUri)
                indexed_objects_counter = indexed_objects_counter + 1

            log.info(f"Successfully indexed {indexed_objects_counter} objects")
            return indexed_objects_counter
    except Exception as e:
        AlarmService().trigger_catalog_indexing_failure_alarm(error=str(e))
        raise e


if __name__ == "__main__":
    ENVNAME = os.environ.get("envname", "local")
    ENGINE = get_engine(envname=ENVNAME)
    ES = connect(envname=ENVNAME)
    index_objects(engine=ENGINE, es=ES)
