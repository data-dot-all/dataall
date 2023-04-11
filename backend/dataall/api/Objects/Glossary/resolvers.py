from datetime import datetime

from sqlalchemy import and_, or_, asc

from .... import db
from ....api.context import Context
from ....db import paginate, exceptions, models
from ....searchproxy import upsert_dataset
from ....searchproxy import upsert_table
from ....searchproxy.indexers import upsert_folder, upsert_dashboard
from ....api.constants import (
    GlossaryRole
)
from dataall.modules.datasets.db.table_column_model import DatasetTableColumn


def resolve_glossary_node(obj: models.GlossaryNode, *_):
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
) -> models.GlossaryNode:
    with context.engine.scoped_session() as session:
        return db.api.Glossary.create_glossary(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=None,
            data=input,
            check_perm=True,
        )


def tree(context: Context, source: models.GlossaryNode):
    if not source:
        return None
    adjency_list = {}
    with context.engine.scoped_session() as session:
        q = session.query(models.GlossaryNode).filter(
            models.GlossaryNode.path.startswith(f'{source.path}/')
        )
        for node in q:
            if not adjency_list.get(node.parentUri):
                adjency_list[node.parentUri] = []


def node_tree(context: Context, source: models.GlossaryNode, filter: dict = None):
    if not source:
        return None
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        q = (
            session.query(models.GlossaryNode)
            .filter(models.GlossaryNode.path.startswith(source.path))
            .filter(models.GlossaryNode.deleted.is_(None))
            .order_by(asc(models.GlossaryNode.path))
        )
        term = filter.get('term')
        nodeType = filter.get('nodeType')
        if term:
            q = q.filter(
                or_(
                    models.GlossaryNode.label.ilike(term),
                    models.GlossaryNode.readme.ilike(term),
                )
            )
        if nodeType:
            q = q.filter(models.GlossaryNode.nodeType == nodeType)

    return paginate(
        q, page_size=filter.get('pageSize', 10), page=filter.get('page', 1)
    ).to_dict()


def list_node_children(
    context: Context, source: models.GlossaryNode, filter: dict = None
):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return db.api.Glossary.list_node_children(session, source, filter)


def create_category(
    context: Context, source, parentUri: str = None, input: dict = None
):
    with context.engine.scoped_session() as session:
        return db.api.Glossary.create_category(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=parentUri,
            data=input,
            check_perm=True,
        )


def create_term(context: Context, source, parentUri: str = None, input: dict = None):
    with context.engine.scoped_session() as session:
        return db.api.Glossary.create_term(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=parentUri,
            data=input,
            check_perm=True,
        )


def list_glossaries(context: Context, source, filter: dict = None):
    if filter is None:
        filter = {}
    with context.engine.scoped_session() as session:
        return db.api.Glossary.list_glossaries(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=None,
            data=filter,
            check_perm=True,
        )


def resolve_categories(
    context: Context, source: models.GlossaryNode, filter: dict = None
):
    if not source:
        return None
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return db.api.Glossary.list_categories(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=source.nodeUri,
            data=filter,
            check_perm=True,
        )


def resolve_terms(context: Context, source: models.GlossaryNode, filter: dict = None):
    if not source:
        return None
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return db.api.Glossary.list_terms(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=source.nodeUri,
            data=filter,
            check_perm=True,
        )


def update_node(
    context: Context, source, nodeUri: str = None, input: dict = None
) -> models.GlossaryNode:
    with context.engine.scoped_session() as session:
        return db.api.Glossary.update_node(
            session,
            username=context.username,
            groups=context.groups,
            uri=nodeUri,
            data=input,
            check_perm=True,
        )


def get_node(context: Context, source, nodeUri: str = None):
    with context.engine.scoped_session() as session:
        node: models.GlossaryNode = session.query(models.GlossaryNode).get(nodeUri)
        if not node:
            raise exceptions.ObjectNotFound('Node', nodeUri)
    return node


def resolve_user_role(context: Context, source: models.GlossaryNode, **kwargs):
    if not source:
        return None
    if source.admin in context.groups:
        return GlossaryRole.Admin.value
    return GlossaryRole.NoPermission.value


def delete_node(context: Context, source, nodeUri: str = None) -> bool:
    with context.engine.scoped_session() as session:
        return db.api.Glossary.delete_node(
            session,
            username=context.username,
            groups=context.groups,
            uri=nodeUri,
            data=None,
            check_perm=True,
        )


def hierarchical_search(context: Context, source, filter: dict = None):
    if not filter:
        filter = {}

    with context.engine.scoped_session() as session:
        return db.api.Glossary.hierarchical_search(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=None,
            data=filter,
            check_perm=True,
        )


def resolve_link(context, source, targetUri: str = None):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        link = (
            session.query(models.TermLink)
            .filter(
                and_(
                    models.TermLink.nodeUri == source.nodeUri,
                    models.TermLink.targetUri == targetUri,
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
        return db.api.Glossary.search_terms(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=None,
            data=filter,
            check_perm=True,
        )


def request_link(
    context: Context,
    source,
    nodeUri: str = None,
    targetUri: str = None,
    targetType: str = None,
):
    with context.engine.scoped_session() as session:
        return db.api.Glossary.link_term(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=nodeUri,
            data={
                'targetUri': targetUri,
                'targetType': targetType,
                'approvedByOwner': True,
                'approvedBySteward': False,
            },
            check_perm=True,
        )


def link_term(
    context: Context,
    source,
    nodeUri: str = None,
    targetUri: str = None,
    targetType: str = None,
):
    with context.engine.scoped_session() as session:
        return db.api.Glossary.link_term(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=nodeUri,
            data={
                'targetUri': targetUri,
                'targetType': targetType,
                'approvedByOwner': True,
                'approvedBySteward': True,
            },
            check_perm=True,
        )


def resolve_term_glossary(context, source: models.GlossaryNode, **kwargs):
    with context.engine.scoped_session() as session:
        parentUri = source.path.split('/')[1]
        return session.query(models.GlossaryNode).get(parentUri)


def get_link(context: Context, source, linkUri: str = None):
    with context.engine.scoped_session() as session:
        link = session.query(models.TermLink).get(linkUri)
        if not link:
            raise exceptions.ObjectNotFound('Link', linkUri)
    return link


def target_union_resolver(obj, *_):
    if isinstance(obj, DatasetTableColumn):
        return 'DatasetTableColumn'
    elif isinstance(obj, models.DatasetTable):
        return 'DatasetTable'
    elif isinstance(obj, models.Dataset):
        return 'Dataset'
    elif isinstance(obj, models.DatasetStorageLocation):
        return 'DatasetStorageLocation'
    elif isinstance(obj, models.Dashboard):
        return 'Dashboard'
    else:
        return None


def resolve_link_target(context, source, **kwargs):
    with context.engine.scoped_session() as session:
        model = {
            'Dataset': models.Dataset,
            'DatasetTable': models.DatasetTable,
            'Column': DatasetTableColumn,
            'DatasetStorageLocation': models.DatasetStorageLocation,
            'Dashboard': models.Dashboard,
        }[source.targetType]
        target = session.query(model).get(source.targetUri)
    return target


def resolve_term_associations(
    context, source: models.GlossaryNode, filter: dict = None
):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return db.api.Glossary.list_term_associations(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=None,
            data={'source': source, 'filter': filter},
            check_perm=True,
        )


def resolve_stats(context, source: models.GlossaryNode, **kwargs):

    with context.engine.scoped_session() as session:
        categories = (
            session.query(models.GlossaryNode)
            .filter(
                and_(
                    models.GlossaryNode.path.startswith(source.path),
                    models.GlossaryNode.nodeType == 'C',
                    models.GlossaryNode.deleted.is_(None),
                )
            )
            .count()
        )
        terms = (
            session.query(models.GlossaryNode)
            .filter(
                and_(
                    models.GlossaryNode.path.startswith(source.path),
                    models.GlossaryNode.nodeType == 'T',
                    models.GlossaryNode.deleted.is_(None),
                )
            )
            .count()
        )

        associations = (
            session.query(models.TermLink)
            .join(
                models.GlossaryNode,
                models.GlossaryNode.nodeType == models.TermLink.nodeUri,
            )
            .filter(models.GlossaryNode.path.startswith(source.path))
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
            session.query(models.TermLink)
            .join(
                models.GlossaryNode,
                models.GlossaryNode.nodeUri == models.TermLink.nodeUri,
            )
            .filter(models.TermLink.targetUri == uri)
        )
        term = filter.get('term')
        if term:
            q = q.filter(
                or_(
                    models.GlossaryNode.label.ilike(term),
                    models.GlossaryNode.readme.ilike(term),
                )
            )
    return paginate(
        q, page=filter.get('page', 1), page_size=filter.get('pageSize', 10)
    ).to_dict()


def resolve_link_node(context: Context, source: models.TermLink, **kwargs):
    with context.engine.scoped_session() as session:
        term = session.query(models.GlossaryNode).get(source.nodeUri)
    return term


def approve_term_association(context: Context, source, linkUri: str = None):
    updated = False
    with context.engine.scoped_session() as session:
        link: models.TermLink = session.query(models.TermLink).get(linkUri)
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
        link: models.TermLink = session.query(models.TermLink).get(linkUri)
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
    glossary_node = session.query(models.GlossaryNode).get(link.nodeUri)
    if glossary_node.owner != username and glossary_node.admin not in groups:
        raise exceptions.UnauthorizedOperation(
            'ASSOCIATE_GLOSSARY_TERM',
            f'User: {username} is not allowed to manage glossary term associations',
        )


def reindex(context, linkUri):
    with context.engine.scoped_session() as session:
        link: models.TermLink = session.query(models.TermLink).get(linkUri)
        if not link:
            return
    target = resolve_link_target(context, source=link)
    if isinstance(target, models.Dataset):
        upsert_dataset(session=session, es=context.es, datasetUri=link.targetUri)
    elif isinstance(target, models.DatasetTable):
        upsert_table(session=session, es=context.es, tableUri=link.targetUri)
    elif isinstance(target, models.DatasetStorageLocation):
        upsert_folder(session=session, es=context.es, locationUri=link.targetUri)
    elif isinstance(target, models.Dashboard):
        upsert_dashboard(session=session, es=context.es, dashboardUri=link.targetUri)
