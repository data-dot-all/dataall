"""Indexes Datasets in OpenSearch"""

from dataall import db
from dataall.db import models
from dataall.modules.datasets.services.dataset_location import DatasetLocationService
from dataall.searchproxy.base_indexer import BaseIndexer


class DatasetIndexer(BaseIndexer):

    @classmethod
    def upsert(cls, session, dataset_uri: str):
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
            .filter(models.Dataset.datasetUri == dataset_uri)
            .first()
        )
        count_tables = db.api.Dataset.count_dataset_tables(session, dataset_uri)
        count_folders = DatasetLocationService.count_dataset_locations(session, dataset_uri)
        count_upvotes = db.api.Vote.count_upvotes(
            session, None, None, dataset_uri, {'targetType': 'dataset'}
        )

        if dataset:
            glossary = BaseIndexer._get_target_glossary_terms(session, dataset_uri)
            BaseIndexer._index(
                doc_id=dataset_uri,
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
