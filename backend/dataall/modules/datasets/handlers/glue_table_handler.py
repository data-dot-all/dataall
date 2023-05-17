import logging

from dataall.aws.handlers.glue import Glue
from dataall.aws.handlers.service_handlers import Worker
from dataall.db import models
from dataall.modules.datasets.aws.glue_dataset_client import DatasetCrawler
from dataall.modules.datasets.services.dataset_table_service import DatasetTableService
from dataall.modules.datasets_base.db.dataset_repository import DatasetRepository
from dataall.modules.datasets_base.db.models import Dataset

log = logging.getLogger(__name__)


class DatasetTableSyncHandler:
    """A handler for dataset table"""

    @staticmethod
    @Worker.handler(path='glue.dataset.database.tables')
    def sync_existing_tables(engine, task: models.Task):
        with engine.scoped_session() as session:
            dataset: Dataset = DatasetRepository.get_dataset_by_uri(
                session, task.targetUri
            )
            tables = DatasetCrawler(dataset).list_glue_database_tables()
            DatasetTableService.sync_existing_tables(session, dataset.datasetUri, glue_tables=tables)
            return tables
