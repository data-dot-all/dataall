import logging
from datetime import datetime

from sqlalchemy import asc, or_, and_, literal
from sqlalchemy.orm import with_expression

from dataall.base.db import exceptions, paginate
from dataall.modules.catalog.db.glossary_models import GlossaryNodeStatus, TermLink, GlossaryNode
from dataall.modules.catalog.indexers.registry import GlossaryRegistry
from dataall.base.db.paginator import Page
from dataall.base.context import get_context

logger = logging.getLogger(__name__)


class GlossaryRepository:
    @staticmethod
    def create_glossary(session, data=None):
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
    def create_category(session, uri, data=None):
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
    def create_term(session, uri, data=None):
        parent: GlossaryNode = session.query(GlossaryNode).get(uri)
        if not parent:
            raise exceptions.ObjectNotFound('Glossary or Category', uri)
        if parent.nodeType not in ['G', 'C']:
            raise exceptions.InvalidInput('Term', uri, 'Category or Glossary are required to create a term')

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
    def list_glossaries(session, data=None):
        q = session.query(GlossaryNode).filter(GlossaryNode.nodeType == 'G', GlossaryNode.deleted.is_(None))
        term = data.get('term')
        if term:
            q = q.filter(
                or_(
                    GlossaryNode.label.ilike('%' + term + '%'),
                    GlossaryNode.readme.ilike('%' + term + '%'),
                )
            )
        return paginate(
            q.order_by(GlossaryNode.label), page_size=data.get('pageSize', 10), page=data.get('page', 1)
        ).to_dict()

    @staticmethod
    def list_node_children(session, path, filter):
        q = (
            session.query(GlossaryNode)
            .filter(GlossaryNode.path.startswith(path + '/'))
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
        return paginate(q, page_size=filter.get('pageSize', 10), page=filter.get('page', 1)).to_dict()

    @staticmethod
    def get_node_tree(session, path, filter):
        q = (
            session.query(GlossaryNode)
            .filter(GlossaryNode.path.startswith(path))
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

        return paginate(q, page_size=filter.get('pageSize', 10), page=filter.get('page', 1)).to_dict()

    @staticmethod
    def get_node_link_to_target(session, username, uri, targetUri):
        link = (
            session.query(TermLink)
            .filter(
                and_(
                    TermLink.nodeUri == uri,
                    TermLink.targetUri == targetUri,
                )
            )
            .first()
        )
        if not link:
            link = {
                'nodeUri': uri,
                'targetUri': targetUri,
                'created': datetime.now().isoformat(),
                'owner': username,
                'approvedByOwner': False,
                'approvedBySteward': False,
            }

        return link

    @staticmethod
    def get_glossary_categories_terms_and_associations(session, path):
        categories = (
            session.query(GlossaryNode)
            .filter(
                and_(
                    GlossaryNode.path.startswith(path),
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
                    GlossaryNode.path.startswith(path),
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
            .filter(GlossaryNode.path.startswith(path))
            .count()
        )

        return {'categories': categories, 'terms': terms, 'associations': associations}

    @staticmethod
    def list_term_associations(session, target_model_definitions, node, filter=None):
        query = None
        subqueries = []
        for definition in target_model_definitions:
            model = definition.model
            subquery = session.query(
                definition.target_uri().label('targetUri'),
                literal(definition.target_type.lower()).label('targetType'),
                model.label.label('label'),
                model.name.label('name'),
                model.description.label('description'),
            )
            if subquery.first() is not None:
                subqueries.append(subquery)

        query = subqueries[0].union(*subqueries[1:])

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
            .join(linked_objects, TermLink.targetUri == linked_objects.c.targetUri)
        )

        if node.nodeType == 'T':
            q = q.filter(TermLink.nodeUri == node.nodeUri)
        elif node.nodeType in ['C', 'G']:
            q = q.filter(GlossaryNode.path.startswith(node.path))
        else:
            raise Exception(f'InvalidNodeType ({node.nodeUri}/{node.nodeType})')

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

        return paginate(q, page=filter.get('page', 1), page_size=filter.get('pageSize', 25)).to_dict()

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
            q.order_by(GlossaryNode.label), page=data.get('page', 1), page_size=data.get('pageSize', 10)
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
            q.order_by(GlossaryNode.label), page=data.get('page', 1), page_size=data.get('pageSize', 10)
        ).to_dict()

    @staticmethod
    def get_node(session, uri) -> GlossaryNode:
        node: GlossaryNode = session.query(GlossaryNode).get(uri)
        if not node:
            raise exceptions.ObjectNotFound('Node', uri)
        return node

    @staticmethod
    def update_node(session, uri, data=None) -> GlossaryNode:
        node: GlossaryNode = session.query(GlossaryNode).get(uri)
        if not node:
            raise exceptions.ObjectNotFound('Node', uri)
        for k in data.keys():
            setattr(node, k, data.get(k))
        return node

    @staticmethod
    def delete_node(session, uri) -> bool:
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
    def approve_term_association(session, username, groups, linkUri: str = None):
        updated = False
        link: TermLink = session.query(TermLink).get(linkUri)
        if not link:
            raise exceptions.ObjectNotFound('Link', linkUri)
        GlossaryRepository._verify_term_association_approver_role(session, username, groups, link)
        if not link.approvedBySteward:
            link.approvedBySteward = True
            updated = True
        GlossaryRepository._reindex(session=session, linkUri=linkUri)
        return updated

    @staticmethod
    def dismiss_term_association(session, username, groups, linkUri: str = None):
        updated = False
        link: TermLink = session.query(TermLink).get(linkUri)
        if not link:
            raise exceptions.ObjectNotFound('Link', linkUri)
        GlossaryRepository._verify_term_association_approver_role(session, username, groups, link)
        if link.approvedBySteward:
            link.approvedBySteward = False
            updated = True
        GlossaryRepository._reindex(session, linkUri=linkUri)
        return updated

    @staticmethod
    def _verify_term_association_approver_role(session, username, groups, link):
        glossary_node = session.query(GlossaryNode).get(link.nodeUri)
        if glossary_node.owner != username and glossary_node.admin not in groups:
            raise exceptions.UnauthorizedOperation(
                'ASSOCIATE_GLOSSARY_TERM',
                f'User: {username} is not allowed to manage glossary term associations',
            )

    @staticmethod
    def _reindex(session, linkUri):
        link: TermLink = session.query(TermLink).get(linkUri)
        if not link:
            return
        GlossaryRegistry.reindex(session, link.targetType, link.targetUri)

    @staticmethod
    def set_glossary_terms_links(session, username, target_uri, target_type, glossary_terms):
        """Used in dependent modules to assign glossary terms to resources"""
        current_links = session.query(TermLink).filter(TermLink.targetUri == target_uri)
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
        """Used in dependent modules get assigned glossary terms to resources"""
        terms = (
            session.query(GlossaryNode)
            .join(TermLink, TermLink.nodeUri == GlossaryNode.nodeUri)
            .filter(
                and_(
                    TermLink.targetUri == target_uri,
                    TermLink.targetType == target_type,
                )
            )
        ).order_by(GlossaryNode.path)

        return paginate(terms, page_size=10000, page=1).to_dict()

    @staticmethod
    def delete_glossary_terms_links(session, target_uri, target_type):
        """Used in dependent modules remove assigned glossary terms to resources"""
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

    @staticmethod
    def search_glossary_terms(session, data=None):
        q = session.query(GlossaryNode).filter(GlossaryNode.deleted.is_(None))
        term = data.get('term')
        if term:
            q = q.filter(
                or_(
                    GlossaryNode.label.ilike(term),
                    GlossaryNode.readme.ilike(term),
                )
            )
        q = q.order_by(asc(GlossaryNode.path))
        return paginate(q, page=data.get('page', 1), page_size=data.get('pageSize', 10)).to_dict()
