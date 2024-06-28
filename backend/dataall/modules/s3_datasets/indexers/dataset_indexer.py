"""Indexes Datasets in OpenSearch"""

import re

from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.organizations.db.organization_repositories import OrganizationRepository
from dataall.modules.vote.db.vote_repositories import VoteRepository
from dataall.modules.s3_datasets.db.dataset_repositories import DatasetRepository
from dataall.modules.s3_datasets.db.dataset_location_repositories import DatasetLocationRepository
from dataall.modules.catalog.indexers.base_indexer import BaseIndexer


class DatasetIndexer(BaseIndexer):
    @classmethod
    def upsert(cls, session, dataset_uri: str):
        dataset = DatasetRepository.get_dataset_by_uri(session, dataset_uri)

        if dataset:
            env = EnvironmentService.get_environment_by_uri(session, dataset.environmentUri)
            org = OrganizationRepository.get_organization_by_uri(session, dataset.organizationUri)

            count_tables = DatasetRepository.count_dataset_tables(session, dataset_uri)
            count_folders = DatasetLocationRepository.count_dataset_locations(session, dataset_uri)
            count_upvotes = VoteRepository.count_upvotes(session, dataset_uri, target_type='dataset')

            glossary = BaseIndexer._get_target_glossary_terms(session, dataset_uri)
            BaseIndexer._index(
                doc_id=dataset_uri,
                doc={
                    'name': dataset.name,
                    'owner': dataset.owner,
                    'label': dataset.label,
                    'admins': dataset.SamlAdminGroupName,
                    'database': dataset.GlueDatabaseName,
                    'source': dataset.S3BucketName,
                    'resourceKind': 'dataset',
                    'description': dataset.description,
                    'classification': re.sub('[^A-Za-z0-9]+', '', dataset.confidentiality),
                    'tags': [t.replace('-', '') for t in dataset.tags or []],
                    'topics': dataset.topics,
                    'region': dataset.region.replace('-', ''),
                    'environmentUri': env.environmentUri,
                    'environmentName': env.name,
                    'organizationUri': org.organizationUri,
                    'organizationName': org.name,
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
