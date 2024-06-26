import logging
import os
import sys

from dataall.modules.catalog.indexers.catalog_indexer import CatalogIndexer
from dataall.modules.catalog.indexers.base_indexer import BaseIndexer
from dataall.base.db import get_engine
from dataall.base.loader import load_modules, ImportMode
from dataall.base.utils.alarm_service import AlarmService

root = logging.getLogger()
root.setLevel(logging.INFO)
if not root.hasHandlers():
    root.addHandler(logging.StreamHandler(sys.stdout))
log = logging.getLogger(__name__)


def index_objects(engine):
    try:
        indexed_object_uris = []
        with engine.scoped_session() as session:
            for indexer in CatalogIndexer.all():
                indexed_object_uris += indexer.index(session)

            log.info(f'Successfully indexed {len(indexed_object_uris)} objects')

            # Search for documents in opensearch without an ID in the indexed_object_uris list
            query = {
                "query": {
                    "bool": {
                        "must_not": {
                            "terms": {
                                "_id": indexed_object_uris
                            }
                        }
                    }
                }
            }

            docs = BaseIndexer.search(query)
            for doc in docs["hits"]["hits"]:
                log.info(f'Deleting document {doc["_id"]}...')
                BaseIndexer.delete_doc(doc_id=doc["_id"])

            log.info(f'Deleted {len(indexed_object_uris)} records')
            return len(indexed_object_uris)
    except Exception as e:
        AlarmService().trigger_catalog_indexing_failure_alarm(error=str(e))
        raise e


if __name__ == '__main__':
    ENVNAME = os.environ.get('envname', 'local')
    ENGINE = get_engine(envname=ENVNAME)

    load_modules({ImportMode.CATALOG_INDEXER_TASK})
    index_objects(engine=ENGINE)
