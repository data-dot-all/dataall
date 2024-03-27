import logging

from dataall.modules.datasets.db.dataset_location_repositories import DatasetLocationRepository
from dataall.modules.datasets.db.dataset_table_repositories import DatasetTableRepository
from dataall.modules.datasets.indexers.dataset_indexer import DatasetIndexer
from dataall.modules.datasets.indexers.location_indexer import DatasetLocationIndexer
from dataall.modules.datasets.indexers.table_indexer import DatasetTableIndexer
from dataall.modules.datasets_base.db.dataset_repositories import DatasetRepository
from dataall.modules.datasets_base.db.dataset_models import Dataset
from dataall.modules.catalog.indexers.catalog_indexer import CatalogIndexer

log = logging.getLogger(__name__)


class DatasetCatalogIndexer(CatalogIndexer):
    """
    Dataset indexer for the catalog. Indexes all tables and folders of datasets
    Register automatically itself when CatalogIndexer instance is created
    """

    def index(self, session) -> int:
        all_datasets: [Dataset] = DatasetRepository.list_all_active_datasets(session)
        log.info(f'Found {len(all_datasets)} datasets')
        indexed = 0
        dataset_count = 0
        for dataset in all_datasets:
            tables = DatasetTableIndexer.upsert_all(session, dataset.datasetUri)
            folders = DatasetLocationIndexer.upsert_all(session, dataset_uri=dataset.datasetUri)
            # Upsert a dataset which doesn't have a table or folder
            if not DatasetTableRepository.find_all_active_tables(session, dataset.datasetUri) and not DatasetLocationRepository.get_dataset_folders(session, dataset.datasetUri):
                DatasetIndexer.upsert(session=session, dataset_uri=dataset.datasetUri)
                dataset_count += 1
            indexed += len(tables) + len(folders) + dataset_count + 1
        return indexed
