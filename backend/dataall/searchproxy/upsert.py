import logging
from datetime import datetime

log = logging.getLogger(__name__)


def upsert(es, index, id, doc):
    doc["_indexed"] = datetime.now()
    if es:
        res = es.index(index=index, id=id, body=doc)
        log.info(f"doc {doc} for id {id} indexed with response {res}")
        return True
    else:
        log.error(f"ES config is missing doc {doc} for id {id} was not indexed")
        return False
