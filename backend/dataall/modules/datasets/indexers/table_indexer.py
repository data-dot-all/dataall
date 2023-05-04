"""Indexes DatasetTable in OpenSearch"""
from operator import and_

from dataall.db import models
from dataall.modules.datasets.db.models import DatasetTable
from dataall.modules.datasets.indexers.dataset_indexer import DatasetIndexer
from dataall.searchproxy.base_indexer import BaseIndexer


class DatasetTableIndexer(BaseIndexer):

    @classmethod
    def upsert(cls, session, table_uri: str):
        table = (
            session.query(
                DatasetTable.datasetUri.label('datasetUri'),
                DatasetTable.tableUri.label('uri'),
                DatasetTable.name.label('name'),
                DatasetTable.owner.label('owner'),
                DatasetTable.label.label('label'),
                DatasetTable.description.label('description'),
                models.Dataset.confidentiality.label('classification'),
                DatasetTable.tags.label('tags'),
                models.Dataset.topics.label('topics'),
                models.Dataset.region.label('region'),
                models.Organization.organizationUri.label('orgUri'),
                models.Organization.name.label('orgName'),
                models.Environment.environmentUri.label('envUri'),
                models.Environment.name.label('envName'),
                models.Dataset.SamlAdminGroupName.label('admins'),
                models.Dataset.GlueDatabaseName.label('database'),
                models.Dataset.S3BucketName.label('source'),
                DatasetTable.created,
                DatasetTable.updated,
                DatasetTable.deleted,
            )
            .join(
                models.Dataset,
                models.Dataset.datasetUri == DatasetTable.datasetUri,
            )
            .join(
                models.Organization,
                models.Dataset.organizationUri == models.Organization.organizationUri,
            )
            .join(
                models.Environment,
                models.Dataset.environmentUri == models.Environment.environmentUri,
            )
            .filter(DatasetTable.tableUri == table_uri)
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

    @classmethod
    def upsert_all(cls, session, dataset_uri: str):
        tables = (
            session.query(DatasetTable)
            .filter(
                and_(
                    DatasetTable.datasetUri == dataset_uri,
                    DatasetTable.LastGlueTableStatus != 'Deleted',
                )
            )
            .all()
        )
        for table in tables:
            DatasetTableIndexer.upsert(session=session, table_uri=table.tableUri)
        return tables

    @classmethod
    def remove_all_deleted(cls, session, dataset_uri: str):
        tables = (
            session.query(DatasetTable)
            .filter(
                and_(
                    DatasetTable.datasetUri == dataset_uri,
                    DatasetTable.LastGlueTableStatus == 'Deleted',
                )
            )
            .all()
        )
        for table in tables:
            cls.delete_doc(doc_id=table.tableUri)
        return tables
