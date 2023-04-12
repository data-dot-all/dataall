import logging
from datetime import datetime

from sqlalchemy import asc, or_, and_, literal, case
from sqlalchemy.orm import with_expression, aliased

from .. import models, exceptions, permissions, paginate, Resource
from .permission_checker import (
    has_tenant_perm,
)
from ..models.Glossary import GlossaryNodeStatus
from dataall.core.glossary.services.registry import GlossaryRegistry

logger = logging.getLogger(__name__)


class Glossary:
    @staticmethod
    @has_tenant_perm(permissions.MANAGE_GLOSSARIES)
    def create_glossary(session, username, groups, uri, data=None, check_perm=None):
        Glossary.validate_params(data)
        g: models.GlossaryNode = models.GlossaryNode(
            label=data.get('label'),
            nodeType='G',
            parentUri='',
            path='/',
            readme=data.get('readme', 'no description available'),
            owner=username,
            admin=data.get('admin'),
            status=GlossaryNodeStatus.approved.value,
        )
        session.add(g)
        session.commit()
        g.path = f'/{g.nodeUri}'
        return g

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_GLOSSARIES)
    def create_category(session, username, groups, uri, data=None, check_perm=None):
        Glossary.validate_params(data)
        parent: models.GlossaryNode = session.query(models.GlossaryNode).get(uri)
        if not parent:
            raise exceptions.ObjectNotFound('Glossary', uri)

        cat = models.GlossaryNode(
            path=parent.path,
            parentUri=parent.nodeUri,
            nodeType='C',
            label=data.get('label'),
            owner=username,
            readme=data.get('readme'),
        )
        session.add(cat)
        session.commit()
        cat.path = parent.path + '/' + cat.nodeUri
        return cat

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_GLOSSARIES)
    def create_term(session, username, groups, uri, data=None, check_perm=None):
        Glossary.validate_params(data)
        parent: models.GlossaryNode = session.query(models.GlossaryNode).get(uri)
        if not parent:
            raise exceptions.ObjectNotFound('Glossary or Category', uri)
        if parent.nodeType not in ['G', 'C']:
            raise exceptions.InvalidInput(
                'Term', uri, 'Category or Glossary are required to create a term'
            )

        term = models.GlossaryNode(
            path=parent.path,
            parentUri=parent.nodeUri,
            nodeType='T',
            label=data.get('label'),
            readme=data.get('readme'),
            owner=username,
        )
        session.add(term)
        session.commit()
        term.path = parent.path + '/' + term.nodeUri
        return term

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_GLOSSARIES)
    def delete_node(session, username, groups, uri, data=None, check_perm=None):
        count = 0
        node: models.GlossaryNode = session.query(models.GlossaryNode).get(uri)
        if not node:
            raise exceptions.ObjectNotFound('Node', uri)
        node.deleted = datetime.now()
        if node.nodeType in ['G', 'C']:
            children = session.query(models.GlossaryNode).filter(
                and_(
                    models.GlossaryNode.path.startswith(node.path),
                    models.GlossaryNode.deleted.is_(None),
                )
            )
            count = children.count() + 1
            children.update({'deleted': datetime.now()}, synchronize_session=False)
        else:
            count = 1
        return count

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_GLOSSARIES)
    def update_node(session, username, groups, uri, data=None, check_perm=None):
        node: models.GlossaryNode = session.query(models.GlossaryNode).get(uri)
        if not node:
            raise exceptions.ObjectNotFound('Node', uri)
        for k in data.keys():
            setattr(node, k, data.get(k))
        return node

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_GLOSSARIES)
    def link_term(session, username, groups, uri, data=None, check_perm=None):
        term: models.GlossaryNode = session.query(models.GlossaryNode).get(uri)
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

        target_model: Resource = GlossaryRegistry.find_model(target_type)
        if not target_model:
            raise exceptions.InvalidInput(
                'NodeType', 'term.nodeType', 'association target type is invalid'
            )

        target = session.query(target_model).get(target_uri)
        if not target:
            raise exceptions.ObjectNotFound('Association target', uri)

        link = models.TermLink(
            owner=username,
            approvedByOwner=data.get('approvedByOwner', True),
            approvedBySteward=data.get('approvedBySteward', True),
            nodeUri=uri,
            targetUri=target_uri,
            targetType=target_type,
        )
        session.add(link)
        return link

    @staticmethod
    def list_glossaries(session, username, groups, uri, data=None, check_perm=None):
        q = session.query(models.GlossaryNode).filter(
            models.GlossaryNode.nodeType == 'G', models.GlossaryNode.deleted.is_(None)
        )
        term = data.get('term')
        if term:
            q = q.filter(
                or_(
                    models.GlossaryNode.label.ilike('%' + term + '%'),
                    models.GlossaryNode.readme.ilike('%' + term + '%'),
                )
            )
        return paginate(
            q, page_size=data.get('pageSize', 10), page=data.get('page', 1)
        ).to_dict()

    @staticmethod
    def list_categories(session, username, groups, uri, data=None, check_perm=None):
        q = session.query(models.GlossaryNode).filter(
            and_(
                models.GlossaryNode.parentUri == uri,
                models.GlossaryNode.nodeType == 'C',
                models.GlossaryNode.deleted.is_(None),
            )
        )

        term = data.get('term')
        if term:
            q = q.filter(
                or_(
                    models.GlossaryNode.label.ilike(term),
                    models.GlossaryNode.readme.ilike(term),
                )
            )
        return paginate(
            q, page=data.get('page', 1), page_size=data.get('pageSize', 10)
        ).to_dict()

    @staticmethod
    def list_terms(session, username, groups, uri, data=None, check_perm=None):
        q = session.query(models.GlossaryNode).filter(
            and_(
                models.GlossaryNode.parentUri == uri,
                models.GlossaryNode.nodeType == 'T',
                models.GlossaryNode.deleted.is_(None),
            )
        )
        term = data.get('term')
        if term:
            q = q.filter(
                or_(
                    models.GlossaryNode.label.ilike(term),
                    models.GlossaryNode.readme.ilike(term),
                )
            )
        return paginate(
            q, page=data.get('page', 1), page_size=data.get('pageSize', 10)
        ).to_dict()

    @staticmethod
    def hierarchical_search(session, username, groups, uri, data=None, check_perm=None):
        q = session.query(models.GlossaryNode).options(
            with_expression(models.GlossaryNode.isMatch, literal(True))
        )
        q = q.filter(models.GlossaryNode.deleted.is_(None))
        term = data.get('term', None)
        if term:
            q = q.filter(
                or_(
                    models.GlossaryNode.label.ilike('%' + term.upper() + '%'),
                    models.GlossaryNode.readme.ilike('%' + term.upper() + '%'),
                )
            )
        matches = q.subquery('matches')
        parents = aliased(models.GlossaryNode, name='parents')
        children = aliased(models.GlossaryNode, name='children')

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
        q = all.order_by(models.GlossaryNode.path)

        return paginate(
            q, page=data.get('page', 1), page_size=data.get('pageSize', 100)
        ).to_dict()

    @staticmethod
    def search_terms(session, username, groups, uri, data=None, check_perm=None):
        q = session.query(models.GlossaryNode).filter(
            models.GlossaryNode.deleted.is_(None)
        )
        term = data.get('term')
        if term:
            q = q.filter(
                or_(
                    models.GlossaryNode.label.ilike(term),
                    models.GlossaryNode.readme.ilike(term),
                )
            )
        q = q.order_by(asc(models.GlossaryNode.path))
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
            session.query(models.GlossaryNode)
            .filter(models.GlossaryNode.path.startswith(source.path + '/'))
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

    @staticmethod
    def list_term_associations(
        session, username, groups, uri, data=None, check_perm=None
    ):
        source = data['source']
        filter = data['filter']
        datasets = session.query(
            models.Dataset.datasetUri.label('targetUri'),
            literal('dataset').label('targetType'),
            models.Dataset.label.label('label'),
            models.Dataset.name.label('name'),
            models.Dataset.description.label('description'),
        )
        tables = session.query(
            models.DatasetTable.tableUri.label('targetUri'),
            literal('table').label('targetType'),
            models.DatasetTable.label.label('label'),
            models.DatasetTable.name.label('name'),
            models.DatasetTable.description.label('description'),
        )
        columns = session.query(
            DatasetTableColumn.columnUri.label('targetUri'),
            literal('column').label('targetType'),
            DatasetTableColumn.label.label('label'),
            DatasetTableColumn.name.label('name'),
            DatasetTableColumn.description.label('description'),
        )
        folders = session.query(
            models.DatasetStorageLocation.locationUri.label('targetUri'),
            literal('folder').label('targetType'),
            models.DatasetStorageLocation.label.label('label'),
            models.DatasetStorageLocation.name.label('name'),
            models.DatasetStorageLocation.description.label('description'),
        )

        dashboards = session.query(
            models.Dashboard.dashboardUri.label('targetUri'),
            literal('dashboard').label('targetType'),
            models.Dashboard.label.label('label'),
            models.Dashboard.name.label('name'),
            models.Dashboard.description.label('description'),
        )

        linked_objects = datasets.union(tables, columns, folders, dashboards).subquery(
            'linked_objects'
        )

        path = models.GlossaryNode.path
        q = (
            session.query(models.TermLink)
            .options(with_expression(models.TermLink.path, path))
            .join(
                models.GlossaryNode,
                models.GlossaryNode.nodeUri == models.TermLink.nodeUri,
            )
            .join(
                linked_objects, models.TermLink.targetUri == linked_objects.c.targetUri
            )
        )
        if source.nodeType == 'T':
            q = q.filter(models.TermLink.nodeUri == source.nodeUri)
        elif source.nodeType in ['C', 'G']:
            q = q.filter(models.GlossaryNode.path.startswith(source.path))
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
        current_links = session.query(models.TermLink).filter(
            models.TermLink.targetUri == target_uri
        )
        for current_link in current_links:
            if current_link not in glossary_terms:
                session.delete(current_link)
        for nodeUri in glossary_terms:

            term = session.query(models.GlossaryNode).get(nodeUri)
            if term:
                link = (
                    session.query(models.TermLink)
                    .filter(
                        models.TermLink.targetUri == target_uri,
                        models.TermLink.nodeUri == nodeUri,
                    )
                    .first()
                )
                if not link:
                    new_link = models.TermLink(
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
            session.query(models.GlossaryNode)
            .join(
                models.TermLink, models.TermLink.nodeUri == models.GlossaryNode.nodeUri
            )
            .filter(
                and_(
                    models.TermLink.targetUri == target_uri,
                    models.TermLink.targetType == target_type,
                )
            )
        )

        return paginate(terms, page_size=10000, page=1).to_dict()

    @staticmethod
    def delete_glossary_terms_links(session, target_uri, target_type):
        term_links = (
            session.query(models.TermLink)
            .filter(
                and_(
                    models.TermLink.targetUri == target_uri,
                    models.TermLink.targetType == target_type,
                )
            )
            .all()
        )
        for link in term_links:
            session.delete(link)
