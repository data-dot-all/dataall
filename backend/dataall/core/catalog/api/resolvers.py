from datetime import datetime

from sqlalchemy import and_, or_, asc

from dataall.core.catalog.api.enums import GlossaryRole
from dataall.core.catalog.api.registry import GlossaryRegistry
from dataall.base.api.context import Context
from dataall.core.catalog.db.glossary import Glossary
from dataall.core.catalog.db.glossary_models import TermLink, GlossaryNode
from dataall.base.db import paginate, exceptions


def resolve_glossary_node(obj: GlossaryNode, *_):
    if obj.nodeType == 'G':
        return 'Glossary'
    elif obj.nodeType == 'C':
        return 'Category'
    elif obj.nodeType == 'T':
        return 'Term'
    else:
        return None


def create_glossary(
    context: Context, source, input: dict = None
) -> GlossaryNode:
    with context.engine.scoped_session() as session:
        return Glossary.create_glossary(session, input)


def tree(context: Context, source: GlossaryNode):
    if not source:
        return None
    adjency_list = {}
    with context.engine.scoped_session() as session:
        q = session.query(GlossaryNode).filter(
            GlossaryNode.path.startswith(f'{source.path}/')
        )
        for node in q:
            if not adjency_list.get(node.parentUri):
                adjency_list[node.parentUri] = []


def node_tree(context: Context, source: GlossaryNode, filter: dict = None):
    if not source:
        return None
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        q = (
            session.query(GlossaryNode)
            .filter(GlossaryNode.path.startswith(source.path))
            .filter(GlossaryNode.deleted.is_(None))
            .order_by(asc(GlossaryNode.path))
        )
        term = filter.get('term')
        nodeType = filter.get('nodeType')
        if term:
            q = q.filter(
                or_(
                    GlossaryNode.label.ilike(term),
                    GlossaryNode.readme.ilike(term),
                )
            )
        if nodeType:
            q = q.filter(GlossaryNode.nodeType == nodeType)

    return paginate(
        q, page_size=filter.get('pageSize', 10), page=filter.get('page', 1)
    ).to_dict()


def list_node_children(
    context: Context, source: GlossaryNode, filter: dict = None
):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return Glossary.list_node_children(session, source, filter)


def create_category(
    context: Context, source, parentUri: str = None, input: dict = None
):
    with context.engine.scoped_session() as session:
        return Glossary.create_category(
            session=session,
            uri=parentUri,
            data=input,
        )


def create_term(context: Context, source, parentUri: str = None, input: dict = None):
    with context.engine.scoped_session() as session:
        return Glossary.create_term(
            session=session,
            uri=parentUri,
            data=input,
        )


def list_glossaries(context: Context, source, filter: dict = None):
    if filter is None:
        filter = {}
    with context.engine.scoped_session() as session:
        return Glossary.list_glossaries(
            session=session,
            data=filter,
        )


def resolve_categories(
    context: Context, source: GlossaryNode, filter: dict = None
):
    if not source:
        return None
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return Glossary.list_categories(
            session=session,
            uri=source.nodeUri,
            data=filter,
        )


def resolve_terms(context: Context, source: GlossaryNode, filter: dict = None):
    if not source:
        return None
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return Glossary.list_terms(
            session=session,
            uri=source.nodeUri,
            data=filter,
        )


def update_node(
    context: Context, source, nodeUri: str = None, input: dict = None
) -> GlossaryNode:
    with context.engine.scoped_session() as session:
        return Glossary.update_node(
            session,
            uri=nodeUri,
            data=input,
        )


def get_node(context: Context, source, nodeUri: str = None):
    with context.engine.scoped_session() as session:
        node: GlossaryNode = session.query(GlossaryNode).get(nodeUri)
        if not node:
            raise exceptions.ObjectNotFound('Node', nodeUri)
    return node


def resolve_user_role(context: Context, source: GlossaryNode, **kwargs):
    if not source:
        return None
    if source.admin in context.groups:
        return GlossaryRole.Admin.value
    return GlossaryRole.NoPermission.value


def delete_node(context: Context, source, nodeUri: str = None) -> bool:
    with context.engine.scoped_session() as session:
        return Glossary.delete_node(session, nodeUri)


def hierarchical_search(context: Context, source, filter: dict = None):
    if not filter:
        filter = {}

    with context.engine.scoped_session() as session:
        return Glossary.hierarchical_search(
            session=session,
            data=filter,
        )


def resolve_link(context, source, targetUri: str = None):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        link = (
            session.query(TermLink)
            .filter(
                and_(
                    TermLink.nodeUri == source.nodeUri,
                    TermLink.targetUri == targetUri,
                )
            )
            .first()
        )
        if not link:
            link = {
                'nodeUri': source.nodeUri,
                'targetUri': targetUri,
                'created': datetime.now().isoformat(),
                'owner': context.username,
                'approvedByOwner': False,
                'approvedBySteward': False,
            }

    return link


def search_terms(context: Context, source, filter: dict = None):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return Glossary.search_terms(
            session=session,
            data=filter,
        )


def request_link(
    context: Context,
    source,
    nodeUri: str = None,
    targetUri: str = None,
    targetType: str = None,
):
    with context.engine.scoped_session() as session:
        return Glossary.link_term(
            session=session,
            uri=nodeUri,
            data={
                'targetUri': targetUri,
                'targetType': targetType,
                'approvedByOwner': True,
                'approvedBySteward': False,
            },
            target_model=_target_model(targetType),
        )


def link_term(
    context: Context,
    source,
    nodeUri: str = None,
    targetUri: str = None,
    targetType: str = None,
):
    with context.engine.scoped_session() as session:
        return Glossary.link_term(
            session=session,
            uri=nodeUri,
            data={
                'targetUri': targetUri,
                'targetType': targetType,
                'approvedByOwner': True,
                'approvedBySteward': True,
            },
            target_model=_target_model(targetType),
        )


def resolve_term_glossary(context, source: GlossaryNode, **kwargs):
    with context.engine.scoped_session() as session:
        parentUri = source.path.split('/')[1]
        return session.query(GlossaryNode).get(parentUri)


def get_link(context: Context, source, linkUri: str = None):
    with context.engine.scoped_session() as session:
        link = session.query(TermLink).get(linkUri)
        if not link:
            raise exceptions.ObjectNotFound('Link', linkUri)
    return link


def target_union_resolver(obj, *_):
    return GlossaryRegistry.find_object_type(obj)


def resolve_link_target(context, source, **kwargs):
    with context.engine.scoped_session() as session:
        model = GlossaryRegistry.find_model(source.targetType)
        target = session.query(model).get(source.targetUri)
    return target


def resolve_term_associations(
    context, source: GlossaryNode, filter: dict = None
):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return Glossary.list_term_associations(
            session=session,
            data={'source': source, 'filter': filter},
            target_model_definitions=GlossaryRegistry.definitions()
        )


def resolve_stats(context, source: GlossaryNode, **kwargs):

    with context.engine.scoped_session() as session:
        categories = (
            session.query(GlossaryNode)
            .filter(
                and_(
                    GlossaryNode.path.startswith(source.path),
                    GlossaryNode.nodeType == 'C',
                    GlossaryNode.deleted.is_(None),
                )
            )
            .count()
        )
        terms = (
            session.query(GlossaryNode)
            .filter(
                and_(
                    GlossaryNode.path.startswith(source.path),
                    GlossaryNode.nodeType == 'T',
                    GlossaryNode.deleted.is_(None),
                )
            )
            .count()
        )

        associations = (
            session.query(TermLink)
            .join(
                GlossaryNode,
                GlossaryNode.nodeType == TermLink.nodeUri,
            )
            .filter(GlossaryNode.path.startswith(source.path))
            .count()
        )

    return {'categories': categories, 'terms': terms, 'associations': associations}


def list_asset_linked_terms(
    context: Context, source, uri: str = None, filter: dict = None
):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        q = (
            session.query(TermLink)
            .join(
                GlossaryNode,
                GlossaryNode.nodeUri == TermLink.nodeUri,
            )
            .filter(TermLink.targetUri == uri)
        )
        term = filter.get('term')
        if term:
            q = q.filter(
                or_(
                    GlossaryNode.label.ilike(term),
                    GlossaryNode.readme.ilike(term),
                )
            )
    return paginate(
        q, page=filter.get('page', 1), page_size=filter.get('pageSize', 10)
    ).to_dict()


def resolve_link_node(context: Context, source: TermLink, **kwargs):
    with context.engine.scoped_session() as session:
        term = session.query(GlossaryNode).get(source.nodeUri)
    return term


def approve_term_association(context: Context, source, linkUri: str = None):
    updated = False
    with context.engine.scoped_session() as session:
        link: TermLink = session.query(TermLink).get(linkUri)
        if not link:
            raise exceptions.ObjectNotFound('Link', linkUri)
        verify_term_association_approver_role(
            session, context.username, context.groups, link
        )
        if not link.approvedBySteward:
            link.approvedBySteward = True
            updated = True
    reindex(context, linkUri=linkUri)
    return updated


def dismiss_term_association(context: Context, source, linkUri: str = None):
    updated = False
    with context.engine.scoped_session() as session:
        link: TermLink = session.query(TermLink).get(linkUri)
        if not link:
            raise exceptions.ObjectNotFound('Link', linkUri)
        verify_term_association_approver_role(
            session, context.username, context.groups, link
        )
        if link.approvedBySteward:
            link.approvedBySteward = False
            updated = True
    reindex(context, linkUri=linkUri)
    return updated


def verify_term_association_approver_role(session, username, groups, link):
    glossary_node = session.query(GlossaryNode).get(link.nodeUri)
    if glossary_node.owner != username and glossary_node.admin not in groups:
        raise exceptions.UnauthorizedOperation(
            'ASSOCIATE_GLOSSARY_TERM',
            f'User: {username} is not allowed to manage glossary term associations',
        )


def reindex(context, linkUri):
    with context.engine.scoped_session() as session:
        link: TermLink = session.query(TermLink).get(linkUri)
        if not link:
            return

    GlossaryRegistry.reindex(session, link.targetType, link.targetUri)


def _target_model(target_type: str):
    target_model = GlossaryRegistry.find_model(target_type)
    if not target_model:
        raise exceptions.InvalidInput(
            'NodeType', 'term.nodeType', 'association target type is invalid'
        )
    return target_model
