import logging

from dataall.aws.handlers.service_handlers import Worker
from dataall.db import models
from dataall.modules.datasets.aws.glue_dataset_client import DatasetCrawler
from dataall.modules.datasets.db.models import Dataset
from dataall.modules.datasets.services.dataset_service import DatasetService

log = logging.getLogger(__name__)


class GlueDatasetHandler:

    @staticmethod
    @Worker.handler(path='glue.crawler.start')
    def start_crawler(engine, task: models.Task):
        with engine.scoped_session() as session:
            dataset: Dataset = DatasetService.get_dataset_by_uri(
                session, task.targetUri
            )
            location = task.payload.get('location')
            targets = {'S3Targets': [{'Path': location}]}
            crawler = DatasetCrawler(dataset)
            if location:
                crawler.update_crawler(targets)
            return crawler.start_crawler()
