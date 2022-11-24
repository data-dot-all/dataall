import logging

from sqlalchemy import and_
from sqlalchemy.orm import with_expression

from .upsert import upsert
from .. import db
from ..db import models

log = logging.getLogger(__name__)


def get_target_glossary_terms(session, targetUri):
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
                models.TermLink.targetUri == targetUri,
                models.TermLink.approvedBySteward.is_(True),
            )
        )
    )
    return [t.path for t in q]


def upsert_dataset(session, es, datasetUri: str):
    dataset = (
        session.query(
            models.Dataset.datasetUri.label('datasetUri'),
            models.Dataset.name.label('name'),
            models.Dataset.owner.label('owner'),
            models.Dataset.label.label('label'),
            models.Dataset.description.label('description'),
            models.Dataset.confidentiality.label('classification'),
            models.Dataset.tags.label('tags'),
            models.Dataset.topics.label('topics'),
            models.Dataset.region.label('region'),
            models.Organization.organizationUri.label('orgUri'),
            models.Organization.name.label('orgName'),
            models.Environment.environmentUri.label('envUri'),
            models.Environment.name.label('envName'),
            models.Dataset.SamlAdminGroupName.label('admins'),
            models.Dataset.GlueDatabaseName.label('database'),
            models.Dataset.S3BucketName.label('source'),
            models.Dataset.created,
            models.Dataset.updated,
            models.Dataset.deleted,
        )
        .join(
            models.Organization,
            models.Dataset.organizationUri == models.Organization.organizationUri,
        )
        .join(
            models.Environment,
            models.Dataset.environmentUri == models.Environment.environmentUri,
        )
        .filter(models.Dataset.datasetUri == datasetUri)
        .first()
    )
    count_tables = db.api.Dataset.count_dataset_tables(session, datasetUri)
    count_folders = db.api.Dataset.count_dataset_locations(session, datasetUri)
    count_upvotes = db.api.Vote.count_upvotes(
        session, None, None, datasetUri, {'targetType': 'dataset'}
    )

    if dataset:
        glossary = get_target_glossary_terms(session, datasetUri)
        upsert(
            es=es,
            index='dataall-index',
            id=datasetUri,
            doc={
                'name': dataset.name,
                'owner': dataset.owner,
                'label': dataset.label,
                'admins': dataset.admins,
                'database': dataset.database,
                'source': dataset.source,
                'resourceKind': 'dataset',
                'description': dataset.description,
                'classification': dataset.classification,
                'tags': [t.replace('-', '') for t in dataset.tags or []],
                'topics': dataset.topics,
                'region': dataset.region.replace('-', ''),
                'environmentUri': dataset.envUri,
                'environmentName': dataset.envName,
                'organizationUri': dataset.orgUri,
                'organizationName': dataset.orgName,
                'created': dataset.created,
                'updated': dataset.updated,
                'deleted': dataset.deleted,
                'glossary': glossary,
                'tables': count_tables,
                'folders': count_folders,
                'upvotes': count_upvotes,
            },
        )
    return dataset


def upsert_table(session, es, tableUri: str):
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
        .filter(models.DatasetTable.tableUri == tableUri)
        .first()
    )

    if table:
        glossary = get_target_glossary_terms(session, tableUri)
        tags = table.tags if table.tags else []
        upsert(
            es=es,
            index='dataall-index',
            id=tableUri,
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
        upsert_dataset(session, es, table.datasetUri)
    return table


def upsert_folder(session, es, locationUri: str):
    folder = (
        session.query(
            models.DatasetStorageLocation.datasetUri.label('datasetUri'),
            models.DatasetStorageLocation.locationUri.label('uri'),
            models.DatasetStorageLocation.name.label('name'),
            models.DatasetStorageLocation.owner.label('owner'),
            models.DatasetStorageLocation.label.label('label'),
            models.DatasetStorageLocation.description.label('description'),
            models.DatasetStorageLocation.tags.label('tags'),
            models.DatasetStorageLocation.region.label('region'),
            models.Organization.organizationUri.label('orgUri'),
            models.Organization.name.label('orgName'),
            models.Environment.environmentUri.label('envUri'),
            models.Environment.name.label('envName'),
            models.Dataset.SamlAdminGroupName.label('admins'),
            models.Dataset.S3BucketName.label('source'),
            models.Dataset.topics.label('topics'),
            models.Dataset.confidentiality.label('classification'),
            models.DatasetStorageLocation.created,
            models.DatasetStorageLocation.updated,
            models.DatasetStorageLocation.deleted,
        )
        .join(
            models.Dataset,
            models.Dataset.datasetUri == models.DatasetStorageLocation.datasetUri,
        )
        .join(
            models.Organization,
            models.Dataset.organizationUri == models.Organization.organizationUri,
        )
        .join(
            models.Environment,
            models.Dataset.environmentUri == models.Environment.environmentUri,
        )
        .filter(models.DatasetStorageLocation.locationUri == locationUri)
        .first()
    )
    if folder:
        glossary = get_target_glossary_terms(session, locationUri)
        upsert(
            es=es,
            index='dataall-index',
            id=locationUri,
            doc={
                'name': folder.name,
                'admins': folder.admins,
                'owner': folder.owner,
                'label': folder.label,
                'resourceKind': 'folder',
                'description': folder.description,
                'source': folder.source,
                'classification': folder.classification,
                'tags': [f.replace('-', '') for f in folder.tags or []],
                'topics': folder.topics,
                'region': folder.region.replace('-', ''),
                'datasetUri': folder.datasetUri,
                'environmentUri': folder.envUri,
                'environmentName': folder.envName,
                'organizationUri': folder.orgUri,
                'organizationName': folder.orgName,
                'created': folder.created,
                'updated': folder.updated,
                'deleted': folder.deleted,
                'glossary': glossary,
            },
        )
        upsert_dataset(session, es, folder.datasetUri)
    return folder


def upsert_dashboard(session, es, dashboardUri: str):
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
        .filter(models.Dashboard.dashboardUri == dashboardUri)
        .first()
    )
    if dashboard:
        glossary = get_target_glossary_terms(session, dashboardUri)
        count_upvotes = db.api.Vote.count_upvotes(
            session, None, None, dashboardUri, {'targetType': 'dashboard'}
        )
        upsert(
            es=es,
            index='dataall-index',
            id=dashboardUri,
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
        upsert_table(session, es, table.tableUri)
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


def upsert_dataset_folders(session, es, datasetUri: str):
    folders = (
        session.query(models.DatasetStorageLocation)
        .filter(models.DatasetStorageLocation.datasetUri == datasetUri)
        .all()
    )
    for folder in folders:
        upsert_folder(session, es, folder.locationUri)
    return folders


def delete_doc(es, doc_id, index='dataall-index'):
    es.delete(index=index, id=doc_id, ignore=[400, 404])
    return True
