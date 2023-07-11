import logging
import os
import sys

from dataall.core.catalog.indexers.catalog_indexer import CatalogIndexer
from dataall.db import get_engine
from dataall.base.loader import load_modules, ImportMode
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
