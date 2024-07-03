from dataall.modules.catalog.api.enums import GlossaryRole
from dataall.modules.catalog.services.glossaries_service import GlossariesService
from dataall.modules.catalog.services.catalog_service import CatalogService
from dataall.base.api.context import Context
from dataall.modules.catalog.db.glossary_models import TermLink, GlossaryNode
from dataall.base.db import exceptions


def _validate_creation_request(data):
    if not data:
        raise exceptions.RequiredParameter(data)
    if not data.get('admin'):
        raise exceptions.RequiredParameter('admin')
    if not data.get('label'):
        raise exceptions.RequiredParameter('label')


def _required_uri(uri):
    if not uri:
        raise exceptions.RequiredParameter('URI')


def _required_path(path):
    if not path:
        raise exceptions.RequiredParameter('PATH')


def create_glossary(context: Context, source, input: dict = None):
    _validate_creation_request(input)
    return GlossariesService.create_glossary(data=input)


def create_category(context: Context, source, parentUri: str = None, input: dict = None):
    _required_uri(parentUri)
    return GlossariesService.create_category(uri=parentUri, data=input)


def create_term(context: Context, source, parentUri: str = None, input: dict = None):
    _required_uri(parentUri)
    return GlossariesService.create_term(uri=parentUri, data=input)


def update_node(context: Context, source, nodeUri: str = None, input: dict = None):
    _required_uri(nodeUri)
    return GlossariesService.update_node(uri=nodeUri, data=input)


def delete_node(context: Context, source, nodeUri: str = None) -> bool:
    _required_uri(nodeUri)
    return GlossariesService.delete_node(uri=nodeUri)


def list_glossaries(context: Context, source, filter: dict = None):
    if filter is None:
        filter = {}
    return GlossariesService.list_glossaries(data=filter)


def get_node(context: Context, source, nodeUri: str = None):
    """Get a node which can be either a glossary, a category, or a term"""
    _required_uri(nodeUri)
    return GlossariesService.get_node(uri=nodeUri)


def resolve_glossary_node(obj: GlossaryNode, *_):
    if obj.nodeType == 'G':
        return 'Glossary'
    elif obj.nodeType == 'C':
        return 'Category'
    elif obj.nodeType == 'T':
        return 'Term'
    else:
        return None


def resolve_user_role(context: Context, source: GlossaryNode, **kwargs):
    if not source:
        return None
    if source.admin in context.groups:
        return GlossaryRole.Admin.value
    return GlossaryRole.NoPermission.value


def resolve_link(context, source, targetUri: str = None):
    _required_uri(source.nodeUri)
    _required_uri(targetUri)
    return GlossariesService.get_node_link_to_target(uri=source.nodeUri, targetUri=targetUri)


def resolve_stats(context, source: GlossaryNode, **kwargs):
    _required_path(source.path)
    return GlossariesService.get_glossary_categories_terms_and_associations(path=source.path)


def resolve_node_tree(context: Context, source: GlossaryNode, filter: dict = None):
    _required_path(source.path)
    if not filter:
        filter = {}
    return GlossariesService.get_node_tree(path=source.path, filter=filter)


def resolve_node_children(context: Context, source: GlossaryNode, filter: dict = None):
    _required_path(source.path)
    if not filter:
        filter = {}
    return GlossariesService.list_node_children(path=source.path, filter=filter)


def resolve_categories(context: Context, source: GlossaryNode, filter: dict = None):
    _required_uri(source.nodeUri)
    if not filter:
        filter = {}
    return GlossariesService.list_categories(uri=source.nodeUri, data=filter)


def resolve_term_associations(context, source: GlossaryNode, filter: dict = None):
    if not filter:
        filter = {}
    return GlossariesService.list_term_associations(node=source, filter=filter)


def resolve_terms(context: Context, source: GlossaryNode, filter: dict = None):
    _required_uri(source.nodeUri)
    if not filter:
        filter = {}
    return GlossariesService.list_terms(uri=source.nodeUri, data=filter)


def resolve_term_glossary(context, source: GlossaryNode, **kwargs):
    _required_path(source.path)
    parentUri = source.path.split('/')[1]
    _required_uri(parentUri)
    return GlossariesService.get_node(uri=parentUri)


def resolve_link_target(context, source, **kwargs):
    _required_uri(source.targetUri)
    return GlossariesService.get_link_target(targetUri=source.targetUri, targetType=source.targetType)


def resolve_link_node(context: Context, source: TermLink, **kwargs):
    with context.engine.scoped_session() as session:
        term = session.query(GlossaryNode).get(source.nodeUri)
    return term


def approve_term_association(context: Context, source, linkUri: str = None):
    _required_uri(linkUri)
    return GlossariesService.approve_term_association(linkUri=linkUri)


def dismiss_term_association(context: Context, source, linkUri: str = None):
    _required_uri(linkUri)
    return GlossariesService.dismiss_term_association(linkUri=linkUri)


def search_glossary(context: Context, source, filter: dict = None):
    if not filter:
        filter = {}
    return GlossariesService.search_glossary_terms(data=filter)


def start_reindex_catalog(context: Context, source, handleDeletes: bool):
    return CatalogService.start_reindex_catalog(with_deletes=handleDeletes)
