"""Indexes DatasetStorageLocation in OpenSearch"""

import re

from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.organizations.db.organization_repositories import OrganizationRepository
from dataall.modules.s3_datasets.db.dataset_location_repositories import DatasetLocationRepository
from dataall.modules.s3_datasets.db.dataset_repositories import DatasetRepository
from dataall.modules.catalog.indexers.base_indexer import BaseIndexer


class DatasetLocationIndexer(BaseIndexer):
    @classmethod
    def upsert(cls, session, folder_uri: str, dataset=None, env=None, org=None):
        folder = DatasetLocationRepository.get_location_by_uri(session, folder_uri)

        if folder:
            dataset = DatasetRepository.get_dataset_by_uri(session, folder.datasetUri) if not dataset else dataset
            env = EnvironmentService.get_environment_by_uri(session, dataset.environmentUri) if not env else env
            org = OrganizationRepository.get_organization_by_uri(session, dataset.organizationUri) if not org else org
            glossary = BaseIndexer._get_target_glossary_terms(session, folder_uri)

            BaseIndexer._index(
                doc_id=folder_uri,
                doc={
                    'name': folder.name,
                    'admins': dataset.SamlAdminGroupName,
                    'owner': folder.owner,
                    'label': folder.label,
                    'resourceKind': 'folder',
                    'description': folder.description,
                    'source': dataset.S3BucketName,
                    'classification': re.sub('[^A-Za-z0-9]+', '', dataset.confidentiality),
                    'tags': [f.replace('-', '') for f in folder.tags or []],
                    'topics': dataset.topics,
                    'region': folder.region.replace('-', ''),
                    'datasetUri': folder.datasetUri,
                    'environmentUri': env.environmentUri,
                    'environmentName': env.name,
                    'organizationUri': org.organizationUri,
                    'organizationName': org.name,
                    'created': folder.created,
                    'updated': folder.updated,
                    'deleted': folder.deleted,
                    'glossary': glossary,
                },
            )
        return folder

    @classmethod
    def upsert_all(cls, session, dataset_uri: str):
        folders = DatasetLocationRepository.get_dataset_folders(session, dataset_uri)
        dataset = DatasetRepository.get_dataset_by_uri(session, dataset_uri)
        env = EnvironmentService.get_environment_by_uri(session, dataset.environmentUri)
        org = OrganizationRepository.get_organization_by_uri(session, dataset.organizationUri)
        for folder in folders:
            DatasetLocationIndexer.upsert(
                session=session, folder_uri=folder.locationUri, dataset=dataset, env=env, org=org
            )
        return folders
