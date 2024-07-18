"""Indexes Datasets in OpenSearch"""

import re

from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.organizations.db.organization_repositories import OrganizationRepository
from dataall.modules.vote.db.vote_repositories import VoteRepository
from dataall.modules.redshift_datasets.db.redshift_dataset_repositories import RedshiftDatasetRepository
from dataall.modules.redshift_datasets.db.redshift_connection_repositories import RedshiftConnectionRepository
from dataall.modules.redshift_datasets.api.connections.enums import RedshiftType
from dataall.modules.catalog.indexers.base_indexer import BaseIndexer


class DatasetIndexer(BaseIndexer):
    @classmethod
    def upsert(cls, session, dataset_uri: str):
        dataset = RedshiftDatasetRepository.get_redshift_dataset_by_uri(session=session, dataset_uri=dataset_uri)
        connection = RedshiftConnectionRepository.find_redshift_connection(session=session, uri=dataset.connectionUri)

        if dataset:
            env = EnvironmentService.get_environment_by_uri(session, dataset.environmentUri)
            org = OrganizationRepository.get_organization_by_uri(session, dataset.organizationUri)

            count_tables = RedshiftDatasetRepository.count_dataset_tables(session=session, dataset_uri=dataset_uri)
            count_upvotes = VoteRepository.count_upvotes(session, dataset_uri, target_type='redshift-dataset')

            glossary = BaseIndexer._get_target_glossary_terms(session, dataset_uri)
            BaseIndexer._index(
                doc_id=dataset_uri,
                doc={
                    'name': dataset.name,
                    'owner': dataset.owner,
                    'label': dataset.label,
                    'admins': dataset.SamlAdminGroupName,
                    'database': connection.database,
                    'schema': dataset.schema,
                    'source': connection.clusterId if connection.redshiftType == RedshiftType.Cluster.value else connection.nameSpaceId,
                    'resourceKind': 'redshiftdataset',
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
                    'upvotes': count_upvotes,
                },
            )
        return dataset
