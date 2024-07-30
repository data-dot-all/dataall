"""Indexes DatasetTable in OpenSearch"""

import re

from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.organizations.db.organization_repositories import OrganizationRepository
from dataall.modules.redshift_datasets.db.redshift_dataset_repositories import RedshiftDatasetRepository
from dataall.modules.redshift_datasets.db.redshift_connection_repositories import RedshiftConnectionRepository
from dataall.modules.redshift_datasets.services.redshift_enums import RedshiftType
from dataall.modules.catalog.indexers.base_indexer import BaseIndexer


class DatasetTableIndexer(BaseIndexer):
    @classmethod
    def upsert(cls, session, table_uri: str, dataset=None, env=None, org=None):
        table = RedshiftDatasetRepository.get_redshift_table_by_uri(session, table_uri)

        if table:
            dataset = (
                RedshiftDatasetRepository.get_redshift_dataset_by_uri(session, table.datasetUri)
                if not dataset
                else dataset
            )
            connection = RedshiftConnectionRepository.get_redshift_connection(session, dataset.connectionUri)
            env = EnvironmentService.get_environment_by_uri(session, dataset.environmentUri) if not env else env
            org = OrganizationRepository.get_organization_by_uri(session, dataset.organizationUri) if not org else org
            glossary = BaseIndexer._get_target_glossary_terms(session, table_uri)

            tags = table.tags if table.tags else []
            BaseIndexer._index(
                doc_id=table_uri,
                doc={
                    'name': table.name,
                    'admins': dataset.SamlAdminGroupName,
                    'owner': table.owner,
                    'label': table.label,
                    'resourceKind': 'redshifttable',
                    'description': table.description,
                    'database': connection.database,
                    'schema': dataset.schema,
                    'source': connection.clusterId
                    if connection.redshiftType == RedshiftType.Cluster.value
                    else connection.nameSpaceId,
                    'classification': re.sub('[^A-Za-z0-9]+', '', dataset.confidentiality),
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
        return table
