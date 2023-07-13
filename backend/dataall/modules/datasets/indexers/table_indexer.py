"""Indexes DatasetTable in OpenSearch"""
from operator import and_

from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.db.api import Organization
from dataall.modules.datasets.db.dataset_table_repository import DatasetTableRepository
from dataall.modules.datasets_base.db.dataset_repository import DatasetRepository
from dataall.modules.datasets_base.db.models import DatasetTable, Dataset
from dataall.modules.datasets.indexers.dataset_indexer import DatasetIndexer
from dataall.searchproxy.base_indexer import BaseIndexer


class DatasetTableIndexer(BaseIndexer):

    @classmethod
    def upsert(cls, session, table_uri: str):
        table = DatasetTableRepository.get_dataset_table_by_uri(session, table_uri)

        if table:
            dataset = DatasetRepository.get_dataset_by_uri(session, table.datasetUri)
            env = EnvironmentService.get_environment_by_uri(session, dataset.environmentUri)
            org = Organization.get_organization_by_uri(session, dataset.organizationUri)
            glossary = BaseIndexer._get_target_glossary_terms(session, table_uri)

            tags = table.tags if table.tags else []
            BaseIndexer._index(
                doc_id=table_uri,
                doc={
                    'name': table.name,
                    'admins': dataset.SamlAdminGroupName,
                    'owner': table.owner,
                    'label': table.label,
                    'resourceKind': 'table',
                    'description': table.description,
                    'database': table.GlueDatabaseName,
                    'source': table.S3BucketName,
                    'classification': dataset.confidentiality,
                    'tags': [t.replace('-', '') for t in tags or []],
                    'topics': dataset.topics,
                    'region': dataset.region.replace('-', ''),
                    'datasetUri': table.datasetUri,
                    'environmentUri': env.environmentUri,
                    'environmentName': env.name,
                    'organizationUri': org.organizationUri,
                    'organizationName': org.name,
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
        tables = DatasetTableRepository.find_all_active_tables(session, dataset_uri)
        for table in tables:
            DatasetTableIndexer.upsert(session=session, table_uri=table.tableUri)
        return tables

    @classmethod
    def remove_all_deleted(cls, session, dataset_uri: str):
        tables = DatasetTableRepository.find_all_deleted_tables(session, dataset_uri)
        for table in tables:
            cls.delete_doc(doc_id=table.tableUri)
        return tables
