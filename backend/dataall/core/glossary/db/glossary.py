import logging
from datetime import datetime

from sqlalchemy import asc, or_, and_, literal, case
from sqlalchemy.orm import with_expression, aliased

from dataall.db import exceptions, permissions, paginate, Resource
from dataall.core.glossary.db.glossary_models import GlossaryNodeStatus, TermLink, GlossaryNode
from dataall.db.paginator import Page
from dataall.base.context import get_context
from dataall.core.permissions.permission_checker import has_tenant_permission

logger = logging.getLogger(__name__)


class Glossary:
    @staticmethod
    @has_tenant_permission(permissions.MANAGE_GLOSSARIES)
    def create_glossary(session, data=None):
        Glossary.validate_params(data)
        g: GlossaryNode = GlossaryNode(
            label=data.get('label'),
            nodeType='G',
            parentUri='',
            path='/',
            readme=data.get('readme', 'no description available'),
            owner=get_context().username,
            admin=data.get('admin'),
            status=GlossaryNodeStatus.approved.value,
        )
        session.add(g)
        session.commit()
        g.path = f'/{g.nodeUri}'
        return g

    @staticmethod
    @has_tenant_permission(permissions.MANAGE_GLOSSARIES)
    def create_category(session, uri, data=None):
        Glossary.validate_params(data)
        parent: GlossaryNode = session.query(GlossaryNode).get(uri)
        if not parent:
            raise exceptions.ObjectNotFound('Glossary', uri)

        cat = GlossaryNode(
            path=parent.path,
            parentUri=parent.nodeUri,
            nodeType='C',
            label=data.get('label'),
            owner=get_context().username,
            readme=data.get('readme'),
        )
        session.add(cat)
        session.commit()
        cat.path = parent.path + '/' + cat.nodeUri
        return cat

    @staticmethod
    @has_tenant_permission(permissions.MANAGE_GLOSSARIES)
    def create_term(session, uri, data=None):
        Glossary.validate_params(data)
        parent: GlossaryNode = session.query(GlossaryNode).get(uri)
        if not parent:
            raise exceptions.ObjectNotFound('Glossary or Category', uri)
        if parent.nodeType not in ['G', 'C']:
            raise exceptions.InvalidInput(
                'Term', uri, 'Category or Glossary are required to create a term'
            )

        term = GlossaryNode(
            path=parent.path,
            parentUri=parent.nodeUri,
            nodeType='T',
            label=data.get('label'),
            readme=data.get('readme'),
            owner=get_context().username,
        )
        session.add(term)
        session.commit()
        term.path = parent.path + '/' + term.nodeUri
        return term

    @staticmethod
    @has_tenant_permission(permissions.MANAGE_GLOSSARIES)
    def delete_node(session, uri):
        count = 0
        node: GlossaryNode = session.query(GlossaryNode).get(uri)
        if not node:
            raise exceptions.ObjectNotFound('Node', uri)
        node.deleted = datetime.now()
        if node.nodeType in ['G', 'C']:
            children = session.query(GlossaryNode).filter(
                and_(
                    GlossaryNode.path.startswith(node.path),
                    GlossaryNode.deleted.is_(None),
                )
            )
            count = children.count() + 1
            children.update({'deleted': datetime.now()}, synchronize_session=False)
        else:
            count = 1
        return count

    @staticmethod
    @has_tenant_permission(permissions.MANAGE_GLOSSARIES)
    def update_node(session, uri, data=None):
        node: GlossaryNode = session.query(GlossaryNode).get(uri)
        if not node:
            raise exceptions.ObjectNotFound('Node', uri)
        for k in data.keys():
            setattr(node, k, data.get(k))
        return node

    @staticmethod
    @has_tenant_permission(permissions.MANAGE_GLOSSARIES)
    def link_term(session, uri, target_model: Resource, data):
        term: GlossaryNode = session.query(GlossaryNode).get(uri)
        if not term:
            raise exceptions.ObjectNotFound('Node', uri)
        if term.nodeType != 'T':
            raise exceptions.InvalidInput(
                'NodeType',
                'term.nodeType',
                'associations are allowed for Glossary terms only',
            )

        target_uri: str = data['targetUri']
        target_type: str = data['targetType']

        target = session.query(target_model).get(target_uri)
        if not target:
            raise exceptions.ObjectNotFound('Association target', uri)

        link = TermLink(
            owner=get_context().username,
            approvedByOwner=data.get('approvedByOwner', True),
            approvedBySteward=data.get('approvedBySteward', True),
            nodeUri=uri,
            targetUri=target_uri,
            targetType=target_type,
        )
        session.add(link)
        return link

    @staticmethod
    def list_glossaries(session, data=None):
        q = session.query(GlossaryNode).filter(
            GlossaryNode.nodeType == 'G', GlossaryNode.deleted.is_(None)
        )
        term = data.get('term')
        if term:
            q = q.filter(
                or_(
                    GlossaryNode.label.ilike('%' + term + '%'),
                    GlossaryNode.readme.ilike('%' + term + '%'),
                )
            )
        return paginate(
            q, page_size=data.get('pageSize', 10), page=data.get('page', 1)
        ).to_dict()

    @staticmethod
    def list_categories(session, uri, data=None):
        q = session.query(GlossaryNode).filter(
            and_(
                GlossaryNode.parentUri == uri,
                GlossaryNode.nodeType == 'C',
                GlossaryNode.deleted.is_(None),
            )
        )

        term = data.get('term')
        if term:
            q = q.filter(
                or_(
                    GlossaryNode.label.ilike(term),
                    GlossaryNode.readme.ilike(term),
                )
            )
        return paginate(
            q, page=data.get('page', 1), page_size=data.get('pageSize', 10)
        ).to_dict()

    @staticmethod
    def list_terms(session, uri, data=None):
        q = session.query(GlossaryNode).filter(
            and_(
                GlossaryNode.parentUri == uri,
                GlossaryNode.nodeType == 'T',
                GlossaryNode.deleted.is_(None),
            )
        )
        term = data.get('term')
        if term:
            q = q.filter(
                or_(
                    GlossaryNode.label.ilike(term),
                    GlossaryNode.readme.ilike(term),
                )
            )
        return paginate(
            q, page=data.get('page', 1), page_size=data.get('pageSize', 10)
        ).to_dict()

    @staticmethod
    def hierarchical_search(session, data=None):
        q = session.query(GlossaryNode).options(
            with_expression(GlossaryNode.isMatch, literal(True))
        )
        q = q.filter(GlossaryNode.deleted.is_(None))
        term = data.get('term', None)
        if term:
            q = q.filter(
                or_(
                    GlossaryNode.label.ilike('%' + term.upper() + '%'),
                    GlossaryNode.readme.ilike('%' + term.upper() + '%'),
                )
            )
        matches = q.subquery('matches')
        parents = aliased(GlossaryNode, name='parents')
        children = aliased(GlossaryNode, name='children')

        if term:
            parent_expr = case(
                [
                    (
                        or_(
                            parents.label.ilike(f'%{term}%'),
                            parents.readme.ilike(f'%{term}%'),
                        )
                    )
                ],
                else_=literal(False),
            )
        else:
            parent_expr = literal(False)

        ascendants = (
            session.query(parents)
            .options(with_expression(parents.isMatch, parent_expr))
            .join(
                and_(
                    matches,
                    matches.c.path.startswith(parents.path),
                    matches,
                    matches.c.deleted.is_(None),
                )
            )
        )

        if term:
            child_expr = case(
                [
                    (
                        or_(
                            children.label.ilike(f'%{term}%'),
                            children.readme.ilike(f'%{term}%'),
                        ),
                        and_(children.deleted.is_(None)),
                    )
                ],
                else_=literal(False),
            )
        else:
            child_expr = literal(False)

        descendants = (
            session.query(children)
            .options(with_expression(children.isMatch, child_expr))
            .join(
                matches,
                children.path.startswith(matches.c.path),
            )
        )

        all = ascendants.union(descendants)
        q = all.order_by(GlossaryNode.path)

        return paginate(
            q, page=data.get('page', 1), page_size=data.get('pageSize', 100)
        ).to_dict()

    @staticmethod
    def search_terms(session, data=None):
        q = session.query(GlossaryNode).filter(
            GlossaryNode.deleted.is_(None)
        )
        term = data.get('term')
        if term:
            q = q.filter(
                or_(
                    GlossaryNode.label.ilike(term),
                    GlossaryNode.readme.ilike(term),
                )
            )
        q = q.order_by(asc(GlossaryNode.path))
        return paginate(
            q, page=data.get('page', 1), page_size=data.get('pageSize', 10)
        ).to_dict()

    @staticmethod
    def validate_params(data):
        if not data:
            exceptions.RequiredParameter('data')
        if not data.get('label'):
            exceptions.RequiredParameter('name')

    @staticmethod
    def list_node_children(session, source, filter):
        q = (
            session.query(GlossaryNode)
            .filter(GlossaryNode.path.startswith(source.path + '/'))
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

    @staticmethod
    def list_term_associations(session, target_model_definitions, data=None):
        source = data['source']
        filter = data['filter']

        query = None
        for definition in target_model_definitions:
            model = definition.model
            subquery = session.query(
                definition.target_uri().label('targetUri'),
                literal(definition.target_type.lower()).label('targetType'),
                model.label.label('label'),
                model.name.label('name'),
                model.description.label('description'),
            )
            if query:
                query.union(subquery)
            else:
                query = subquery

        if query is None:
            return Page([], 1, 1, 0)  # empty page. All modules are turned off

        linked_objects = query.subquery('linked_objects')

        path = GlossaryNode.path
        q = (
            session.query(TermLink)
            .options(with_expression(TermLink.path, path))
            .join(
                GlossaryNode,
                GlossaryNode.nodeUri == TermLink.nodeUri,
            )
            .join(
                linked_objects, TermLink.targetUri == linked_objects.c.targetUri
            )
        )
        if source.nodeType == 'T':
            q = q.filter(TermLink.nodeUri == source.nodeUri)
        elif source.nodeType in ['C', 'G']:
            q = q.filter(GlossaryNode.path.startswith(source.path))
        else:
            raise Exception(f'InvalidNodeType ({source.nodeUri}/{source.nodeType})')

        term = filter.get('term')
        if term:
            q = q.filter(
                or_(
                    linked_objects.c.label.ilike('%' + term + '%'),
                    linked_objects.c.description.ilike(f'%{term}'),
                    linked_objects.c.targetType.ilike(f'%{term}'),
                )
            )
        q = q.order_by(asc(path))

        return paginate(
            q, page=filter.get('page', 1), page_size=filter.get('pageSize', 25)
        ).to_dict()

    @staticmethod
    def set_glossary_terms_links(
        session, username, target_uri, target_type, glossary_terms
    ):
        current_links = session.query(TermLink).filter(
            TermLink.targetUri == target_uri
        )
        for current_link in current_links:
            if current_link not in glossary_terms:
                session.delete(current_link)
        for nodeUri in glossary_terms:

            term = session.query(GlossaryNode).get(nodeUri)
            if term:
                link = (
                    session.query(TermLink)
                    .filter(
                        TermLink.targetUri == target_uri,
                        TermLink.nodeUri == nodeUri,
                    )
                    .first()
                )
                if not link:
                    new_link = TermLink(
                        targetUri=target_uri,
                        nodeUri=nodeUri,
                        targetType=target_type,
                        owner=username,
                        approvedByOwner=True,
                    )
                    session.add(new_link)
                    session.commit()

    @staticmethod
    def get_glossary_terms_links(session, target_uri, target_type):
        terms = (
            session.query(GlossaryNode)
            .join(
                TermLink, TermLink.nodeUri == GlossaryNode.nodeUri
            )
            .filter(
                and_(
                    TermLink.targetUri == target_uri,
                    TermLink.targetType == target_type,
                )
            )
        )

        return paginate(terms, page_size=10000, page=1).to_dict()

    @staticmethod
    def delete_glossary_terms_links(session, target_uri, target_type):
        term_links = (
            session.query(TermLink)
            .filter(
                and_(
                    TermLink.targetUri == target_uri,
                    TermLink.targetType == target_type,
                )
            )
            .all()
        )
        for link in term_links:
            session.delete(link)
