import logging

from sqlalchemy import and_

from .. import db
from ..db import models
from dataall.searchproxy.upsert import BaseIndexer
from dataall.modules.datasets.indexers.dataset_indexer import DatasetIndexer

log = logging.getLogger(__name__)


class DatasetTableIndexer(BaseIndexer):

    @classmethod
    def upsert(cls, session, table_uri: str):
        table = (
            session.query(
                models.DatasetTable.datasetUri.label('datasetUri'),
                models.DatasetTable.tableUri.label('uri'),
                models.DatasetTable.name.label('name'),
                models.DatasetTable.owner.label('owner'),
                models.DatasetTable.label.label('label'),
                models.DatasetTable.description.label('description'),
                models.Dataset.confidentiality.label('classification'),
                models.DatasetTable.tags.label('tags'),
                models.Dataset.topics.label('topics'),
                models.Dataset.region.label('region'),
                models.Organization.organizationUri.label('orgUri'),
                models.Organization.name.label('orgName'),
                models.Environment.environmentUri.label('envUri'),
                models.Environment.name.label('envName'),
                models.Dataset.SamlAdminGroupName.label('admins'),
                models.Dataset.GlueDatabaseName.label('database'),
                models.Dataset.S3BucketName.label('source'),
                models.DatasetTable.created,
                models.DatasetTable.updated,
                models.DatasetTable.deleted,
            )
            .join(
                models.Dataset,
                models.Dataset.datasetUri == models.DatasetTable.datasetUri,
            )
            .join(
                models.Organization,
                models.Dataset.organizationUri == models.Organization.organizationUri,
            )
            .join(
                models.Environment,
                models.Dataset.environmentUri == models.Environment.environmentUri,
            )
            .filter(models.DatasetTable.tableUri == table_uri)
            .first()
        )

        if table:
            glossary = BaseIndexer._get_target_glossary_terms(session, table_uri)
            tags = table.tags if table.tags else []
            BaseIndexer._index(
                doc_id=table_uri,
                doc={
                    'name': table.name,
                    'admins': table.admins,
                    'owner': table.owner,
                    'label': table.label,
                    'resourceKind': 'table',
                    'description': table.description,
                    'database': table.database,
                    'source': table.source,
                    'classification': table.classification,
                    'tags': [t.replace('-', '') for t in tags or []],
                    'topics': table.topics,
                    'region': table.region.replace('-', ''),
                    'datasetUri': table.datasetUri,
                    'environmentUri': table.envUri,
                    'environmentName': table.envName,
                    'organizationUri': table.orgUri,
                    'organizationName': table.orgName,
                    'created': table.created,
                    'updated': table.updated,
                    'deleted': table.deleted,
                    'glossary': glossary,
                },
            )
            DatasetIndexer.upsert(session=session, dataset_uri=table.datasetUri)
        return table


class DashboardIndexer(BaseIndexer):
    @classmethod
    def upsert(cls, session, dashboard_uri: str):
        dashboard = (
            session.query(
                models.Dashboard.dashboardUri.label('uri'),
                models.Dashboard.name.label('name'),
                models.Dashboard.owner.label('owner'),
                models.Dashboard.label.label('label'),
                models.Dashboard.description.label('description'),
                models.Dashboard.tags.label('tags'),
                models.Dashboard.region.label('region'),
                models.Organization.organizationUri.label('orgUri'),
                models.Organization.name.label('orgName'),
                models.Environment.environmentUri.label('envUri'),
                models.Environment.name.label('envName'),
                models.Dashboard.SamlGroupName.label('admins'),
                models.Dashboard.created,
                models.Dashboard.updated,
                models.Dashboard.deleted,
            )
            .join(
                models.Organization,
                models.Dashboard.organizationUri == models.Dashboard.organizationUri,
            )
            .join(
                models.Environment,
                models.Dashboard.environmentUri == models.Environment.environmentUri,
            )
            .filter(models.Dashboard.dashboardUri == dashboard_uri)
            .first()
        )
        if dashboard:
            glossary = BaseIndexer._get_target_glossary_terms(session, dashboard_uri)
            count_upvotes = db.api.Vote.count_upvotes(
                session, None, None, dashboard_uri, {'targetType': 'dashboard'}
            )
            BaseIndexer._index(
                doc_id=dashboard_uri,
                doc={
                    'name': dashboard.name,
                    'admins': dashboard.admins,
                    'owner': dashboard.owner,
                    'label': dashboard.label,
                    'resourceKind': 'dashboard',
                    'description': dashboard.description,
                    'tags': [f.replace('-', '') for f in dashboard.tags or []],
                    'topics': [],
                    'region': dashboard.region.replace('-', ''),
                    'environmentUri': dashboard.envUri,
                    'environmentName': dashboard.envName,
                    'organizationUri': dashboard.orgUri,
                    'organizationName': dashboard.orgName,
                    'created': dashboard.created,
                    'updated': dashboard.updated,
                    'deleted': dashboard.deleted,
                    'glossary': glossary,
                    'upvotes': count_upvotes,
                },
            )
        return dashboard


def upsert_dataset_tables(session, es, datasetUri: str):
    tables = (
        session.query(models.DatasetTable)
        .filter(
            and_(
                models.DatasetTable.datasetUri == datasetUri,
                models.DatasetTable.LastGlueTableStatus != 'Deleted',
            )
        )
        .all()
    )
    for table in tables:
        DatasetTableIndexer.upsert(session=session, table_uri=table.tableUri)
    return tables


def remove_deleted_tables(session, es, datasetUri: str):
    tables = (
        session.query(models.DatasetTable)
        .filter(
            and_(
                models.DatasetTable.datasetUri == datasetUri,
                models.DatasetTable.LastGlueTableStatus == 'Deleted',
            )
        )
        .all()
    )
    for table in tables:
        delete_doc(es, doc_id=table.tableUri)
    return tables


def delete_doc(es, doc_id, index='dataall-index'):
    es.delete(index=index, id=doc_id, ignore=[400, 404])
    return True
