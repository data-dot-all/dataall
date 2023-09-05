import json
import logging

from dataall.base.context import get_context
from dataall.core.permissions.permission_checker import has_tenant_permission

from dataall.modules.catalog.db.glossary_repositories import GlossaryRepository
from dataall.modules.catalog.db.glossary_models import TermLink, GlossaryNode
from dataall.modules.catalog.services.glossaries_permissions import (
    MANAGE_GLOSSARIES
)
logger = logging.getLogger(__name__)


def _session():
    return get_context().db_engine.scoped_session()


class GlossariesService:

    @staticmethod
    @has_tenant_permission(MANAGE_GLOSSARIES)
    def create_glossary(data: dict = None) -> GlossaryNode:
        with _session() as session:
            return GlossaryRepository.create_glossary(session=session, data=data)

    @staticmethod
    @has_tenant_permission(MANAGE_GLOSSARIES)
    def create_category(uri: str, data: dict = None):
        with _session() as session:
            return GlossaryRepository.create_category(session=session, uri=uri, data=data
    )

    @has_tenant_permission(MANAGE_GLOSSARIES)
    @staticmethod
    def create_term(uri: str, data: dict = None):
        with _session() as session:
            return GlossaryRepository.create_term(session=session, uri=uri, data=data)

