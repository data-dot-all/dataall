import logging
from dataall.modules.datasets_base.db.dataset_repositories import DatasetListRepository
from dataall.modules.datasets_base.services.datasets_enums import DatasetType
from dataall.modules.s3_datasets.indexers.dataset_indexer import DatasetIndexer
from dataall.modules.s3_datasets.indexers.location_indexer import DatasetLocationIndexer
from dataall.modules.s3_datasets.indexers.table_indexer import DatasetTableIndexer
from dataall.modules.s3_datasets.db.dataset_models import S3Dataset
from dataall.modules.catalog.indexers.catalog_indexer import CatalogIndexer

log = logging.getLogger(__name__)


class DatasetCatalogIndexer(CatalogIndexer): #TODO: maybe move to datasets_base
    """
    Dataset indexer for the catalog. Indexes all tables and folders of datasets
    Register automatically itself when CatalogIndexer instance is created
    """

    def index(self, session) -> int:
        all_datasets: [S3Dataset] = DatasetListRepository.list_all_active_datasets(session=session, dataset_type=DatasetType.S3)
        log.info(f'Found {len(all_datasets)} datasets')
        indexed = 0
        for dataset in all_datasets:
            tables = DatasetTableIndexer.upsert_all(session, dataset.datasetUri)
            folders = DatasetLocationIndexer.upsert_all(session, dataset_uri=dataset.datasetUri)
            DatasetIndexer.upsert(session=session, dataset_uri=dataset.datasetUri)
            indexed += len(tables) + len(folders) + 1
        return indexed
