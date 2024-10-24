import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from operator import and_

from sqlalchemy.orm import with_expression

from dataall.modules.catalog.db.glossary_models import GlossaryNode, TermLink
from dataall.base.searchproxy import connect

log = logging.getLogger(__name__)


class BaseIndexer(ABC):
    """API to work with OpenSearch"""

    _INDEX = 'dataall-index'
    _es = None
    _QUERY_SIZE = 1000

    @classmethod
    def es(cls):
        """Lazy creation of the OpenSearch connection"""
        if cls._es is None:
            es = connect(envname=os.getenv('envname', 'local'))
            if not es:
                raise Exception('Failed to create ES connection')
            cls._es = es

        return cls._es

    @staticmethod
    @abstractmethod
    def upsert(session, target_id):
        raise NotImplementedError('Method upsert is not implemented')

    @classmethod
    def delete_doc(cls, doc_id):
        es = cls.es()
        es.delete(index=cls._INDEX, id=doc_id, ignore=[400, 404])
        return True

    @classmethod
    def _index(cls, doc_id, doc):
        es = cls.es()
        doc['_indexed'] = datetime.now()
        if es:
            res = es.index(index=cls._INDEX, id=doc_id, body=doc)
            log.info(f'doc {doc} for id {doc_id} indexed with response {res}')
            return True
        else:
            log.error(f'ES config is missing doc {doc} for id {doc_id} was not indexed')
            return False

    @classmethod
    def search_all(cls, query, sort):
        all_results = []
        search_after = None
        while True:
            if search_after:
                query['search_after'] = search_after

            response = BaseIndexer.search(query=query, sort=sort)
            hits = response['hits']['hits']
            if not hits:
                break  # No more results

            all_results.extend(hits)

            # Update search_after for the next iteration
            search_after = hits[-1]['sort']

        return all_results

    @classmethod
    def search(cls, query, sort=None):
        es = cls.es()
        if es:
            res = es.search(index=cls._INDEX, body=query, sort=sort, size=cls._QUERY_SIZE)
            log.info(f'Search query {query} found {res["hits"]["total"]["value"]} total records')
            return res
        else:
            log.error(f'ES config is missing, search query {query} failed')
            return {}

    @staticmethod
    def _get_target_glossary_terms(session, target_uri):
        q = (
            session.query(TermLink)
            .options(
                with_expression(TermLink.path, GlossaryNode.path),
                with_expression(TermLink.label, GlossaryNode.label),
                with_expression(TermLink.readme, GlossaryNode.readme),
            )
            .join(GlossaryNode, GlossaryNode.nodeUri == TermLink.nodeUri)
            .filter(
                and_(
                    TermLink.targetUri == target_uri,
                    TermLink.approvedBySteward.is_(True),
                )
            )
        )
        return [t.path for t in q]
