"""Indexes DatasetStorageLocation in OpenSearch"""
from dataall.modules.datasets.db.models import DatasetStorageLocation

from dataall.db import models
from dataall.modules.datasets.indexers.dataset_indexer import DatasetIndexer
from dataall.searchproxy.upsert import BaseIndexer


class DatasetLocationIndexer(BaseIndexer):

    @classmethod
    def upsert(cls, session, folder_uri: str):
        folder = (
            session.query(
                DatasetStorageLocation.datasetUri.label('datasetUri'),
                DatasetStorageLocation.locationUri.label('uri'),
                DatasetStorageLocation.name.label('name'),
                DatasetStorageLocation.owner.label('owner'),
                DatasetStorageLocation.label.label('label'),
                DatasetStorageLocation.description.label('description'),
                DatasetStorageLocation.tags.label('tags'),
                DatasetStorageLocation.region.label('region'),
                models.Organization.organizationUri.label('orgUri'),
                models.Organization.name.label('orgName'),
                models.Environment.environmentUri.label('envUri'),
                models.Environment.name.label('envName'),
                models.Dataset.SamlAdminGroupName.label('admins'),
                models.Dataset.S3BucketName.label('source'),
                models.Dataset.topics.label('topics'),
                models.Dataset.confidentiality.label('classification'),
                DatasetStorageLocation.created,
                DatasetStorageLocation.updated,
                DatasetStorageLocation.deleted,
            )
            .join(
                models.Dataset,
                models.Dataset.datasetUri == DatasetStorageLocation.datasetUri,
            )
            .join(
                models.Organization,
                models.Dataset.organizationUri == models.Organization.organizationUri,
            )
            .join(
                models.Environment,
                models.Dataset.environmentUri == models.Environment.environmentUri,
            )
            .filter(DatasetStorageLocation.locationUri == folder_uri)
            .first()
        )
        if folder:
            glossary = BaseIndexer._get_target_glossary_terms(session, folder_uri)
            BaseIndexer._index(
                doc_id=folder_uri,
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
            DatasetIndexer.upsert(session=session, dataset_uri=folder.datasetUri)
        return folder

    @classmethod
    def upsert_all(cls, session, dataset_uri: str):
        folders = (
            session.query(DatasetStorageLocation)
            .filter(DatasetStorageLocation.datasetUri == dataset_uri)
            .all()
        )
        for folder in folders:
            DatasetLocationIndexer.upsert(session=session, folder_uri=folder.locationUri)
        return folders
