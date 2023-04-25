import logging

from dataall.aws.handlers.glue import Glue
from dataall.aws.handlers.service_handlers import Worker
from dataall.db import models
from dataall.modules.datasets.db.models import Dataset
from dataall.modules.datasets.services.dataset_service import DatasetService
from dataall.modules.datasets.services.dataset_table import DatasetTableService

log = logging.getLogger(__name__)


class DatasetColumnGlueHandler:
    """A handler for dataset table"""

    @staticmethod
    @Worker.handler(path='glue.dataset.database.tables')
    def list_tables(engine, task: models.Task):
        with engine.scoped_session() as session:
            dataset: Dataset = DatasetService.get_dataset_by_uri(
                session, task.targetUri
            )
            account_id = dataset.AwsAccountId
            region = dataset.region
            tables = Glue.list_glue_database_tables(
                account_id, dataset.GlueDatabaseName, region
            )
            DatasetTableService.sync_existing_tables(session, dataset.datasetUri, glue_tables=tables)
            return tables
