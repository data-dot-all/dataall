import logging
from functools import wraps

from dataall.base.context import get_context
from dataall.base.db import exceptions
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService
from dataall.modules.catalog.db.glossary_models import GlossaryNode
from dataall.modules.catalog.db.glossary_repositories import GlossaryRepository
from dataall.modules.catalog.indexers.registry import GlossaryRegistry
from dataall.modules.catalog.services.glossaries_permissions import MANAGE_GLOSSARIES

logger = logging.getLogger(__name__)


def _session():
    return get_context().db_engine.scoped_session()


class GlossariesResourceAccess:
    @staticmethod
    def is_owner():
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                uri = kwargs.get('uri')
                if not uri:
                    raise KeyError(f"{f.__name__} doesn't have parameter uri.")
                GlossariesResourceAccess.check_owner(uri)
                return f(*args, **kwargs)

            return wrapper

        return decorator

    @staticmethod
    def check_owner(uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            node = GlossaryRepository.get_node(session=session, uri=uri)
            MAX_GLOSSARY_DEPTH = 10
            depth = 0
            while node.nodeType != 'G' and depth <= MAX_GLOSSARY_DEPTH:
                node = GlossaryRepository.get_node(session=session, uri=node.parentUri)
                depth += 1
            if not node or node.admin not in context.groups:
                raise exceptions.UnauthorizedOperation(
                    action='GLOSSARY MUTATION',
                    message=f'User {context.username} is not the admin of the glossary {node.label}.',
                )


class GlossariesService:
    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_GLOSSARIES)
    def create_glossary(data: dict = None) -> GlossaryNode:
        with _session() as session:
            return GlossaryRepository.create_glossary(session=session, data=data)

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_GLOSSARIES)
    @GlossariesResourceAccess.is_owner()
    def create_category(uri: str, data: dict = None):
        with _session() as session:
            return GlossaryRepository.create_category(session=session, uri=uri, data=data)

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_GLOSSARIES)
    @GlossariesResourceAccess.is_owner()
    def create_term(uri: str, data: dict = None):
        with _session() as session:
            return GlossaryRepository.create_term(session=session, uri=uri, data=data)

    @staticmethod
    def list_glossaries(data: dict = None):
        with _session() as session:
            return GlossaryRepository.list_glossaries(session=session, data=data)

    @staticmethod
    def list_categories(uri: str, data: dict = None):
        with _session() as session:
            return GlossaryRepository.list_categories(session=session, uri=uri, data=data)

    @staticmethod
    def list_terms(uri: str, data: dict = None):
        with _session() as session:
            return GlossaryRepository.list_terms(session=session, uri=uri, data=data)

    @staticmethod
    def list_node_children(path: str, filter: dict = None):
        with _session() as session:
            return GlossaryRepository.list_node_children(session=session, path=path, filter=filter)

    @staticmethod
    def get_node_tree(path: str, filter: dict = None):
        with _session() as session:
            return GlossaryRepository.get_node_tree(session=session, path=path, filter=filter)

    @staticmethod
    def get_node_link_to_target(
        uri: str,
        targetUri: str,
    ):
        with _session() as session:
            return GlossaryRepository.get_node_link_to_target(
                session=session, username=get_context().username, uri=uri, targetUri=targetUri
            )

    @staticmethod
    def get_glossary_categories_terms_and_associations(path: str):
        with _session() as session:
            return GlossaryRepository.get_glossary_categories_terms_and_associations(session=session, path=path)

    @staticmethod
    def list_term_associations(node: GlossaryNode, filter: dict = None):
        with _session() as session:
            return GlossaryRepository.list_term_associations(
                session=session, node=node, filter=filter, target_model_definitions=GlossaryRegistry.definitions()
            )

    @staticmethod
    def get_node(uri: str):
        with _session() as session:
            return GlossaryRepository.get_node(session=session, uri=uri)

    @staticmethod
    def get_link_target(targetUri: str, targetType: str):
        with _session() as session:
            model = GlossaryRegistry.find_model(targetType)
            target = session.query(model).get(targetUri)
        return target

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_GLOSSARIES)
    @GlossariesResourceAccess.is_owner()
    def update_node(uri: str = None, data: dict = None):
        with _session() as session:
            return GlossaryRepository.update_node(session=session, uri=uri, data=data)

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_GLOSSARIES)
    @GlossariesResourceAccess.is_owner()
    def delete_node(uri: str = None):
        with _session() as session:
            return GlossaryRepository.delete_node(session=session, uri=uri)

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_GLOSSARIES)
    def approve_term_association(linkUri: str):
        # is_owner permissions checked in GlossaryRepository.approve_term_association
        with _session() as session:
            return GlossaryRepository.approve_term_association(
                session=session, username=get_context().username, groups=get_context().groups, linkUri=linkUri
            )

    @staticmethod
    @TenantPolicyService.has_tenant_permission(MANAGE_GLOSSARIES)
    def dismiss_term_association(linkUri: str):
        # is_owner permissions checked in GlossaryRepository.dismiss_term_association
        with _session() as session:
            return GlossaryRepository.dismiss_term_association(
                session=session, username=get_context().username, groups=get_context().groups, linkUri=linkUri
            )

    @staticmethod
    def search_glossary_terms(data: dict = None):
        with _session() as session:
            return GlossaryRepository.search_glossary_terms(session=session, data=data)
