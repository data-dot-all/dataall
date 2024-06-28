import logging

from typing import List
from dataall.modules.s3_datasets.indexers.dataset_indexer import DatasetIndexer
from dataall.modules.s3_datasets.indexers.location_indexer import DatasetLocationIndexer
from dataall.modules.s3_datasets.indexers.table_indexer import DatasetTableIndexer
from dataall.modules.s3_datasets.db.dataset_repositories import DatasetRepository
from dataall.modules.s3_datasets.db.dataset_models import S3Dataset
from dataall.modules.catalog.indexers.catalog_indexer import CatalogIndexer

log = logging.getLogger(__name__)


class DatasetCatalogIndexer(CatalogIndexer):
    """
    Dataset indexer for the catalog. Indexes all tables and folders of datasets
    Register automatically itself when CatalogIndexer instance is created
    """

    def index(self, session) -> List[str]:
        all_datasets: List[S3Dataset] = DatasetRepository.list_all_active_datasets(session)
        all_dataset_uris = []
        log.info(f'Found {len(all_datasets)} datasets')
        for dataset in all_datasets:
            tables = DatasetTableIndexer.upsert_all(session, dataset.datasetUri)
            all_dataset_uris += [table.tableUri for table in tables]

            folders = DatasetLocationIndexer.upsert_all(session, dataset_uri=dataset.datasetUri)
            all_dataset_uris += [folder.locationUri for folder in folders]

            DatasetIndexer.upsert(session=session, dataset_uri=dataset.datasetUri)
            all_dataset_uris.append(dataset.datasetUri)

        return all_dataset_uris
