import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from operator import and_

from sqlalchemy.orm import with_expression

from dataall.db import models
from dataall.searchproxy import connect

log = logging.getLogger(__name__)


class BaseIndexer(ABC):
    """API to work with OpenSearch"""
    _INDEX = 'dataall-index'
    _es = None

    @classmethod
    def es(cls):
        """Lazy creation of the OpenSearch connection"""
        if cls._es is None:
            cls._es = connect(envname=os.getenv('envname', 'local'))

        return cls._es

    @staticmethod
    @abstractmethod
    def upsert(session, target_id):
        raise NotImplementedError("Method upsert is not implemented")

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
            res = es.index(index=BaseIndexer._INDEX, id=doc_id, body=doc)
            log.info(f'doc {doc} for id {doc_id} indexed with response {res}')
            return True
        else:
            log.error(f'ES config is missing doc {doc} for id {doc_id} was not indexed')
            return False

    @staticmethod
    def _get_target_glossary_terms(session, target_uri):
        q = (
            session.query(models.TermLink)
            .options(
                with_expression(models.TermLink.path, models.GlossaryNode.path),
                with_expression(models.TermLink.label, models.GlossaryNode.label),
                with_expression(models.TermLink.readme, models.GlossaryNode.readme),
            )
            .join(
                models.GlossaryNode, models.GlossaryNode.nodeUri == models.TermLink.nodeUri
            )
            .filter(
                and_(
                    models.TermLink.targetUri == target_uri,
                    models.TermLink.approvedBySteward.is_(True),
                )
            )
        )
        return [t.path for t in q]

