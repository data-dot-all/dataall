import logging

from dataall.core.tasks.service_handlers import Worker
from dataall.core.tasks.db.task_models import Task
from dataall.modules.datasets.aws.glue_dataset_client import DatasetCrawler
from dataall.modules.datasets_base.db.dataset_repositories import DatasetRepository
from dataall.modules.datasets_base.db.dataset_models import Dataset

log = logging.getLogger(__name__)


class DatasetCrawlerHandler:
    @staticmethod
    @Worker.handler(path='glue.crawler.start')
    def start_crawler(engine, task: Task):
        with engine.scoped_session() as session:
            dataset: Dataset = DatasetRepository.get_dataset_by_uri(session, task.targetUri)
            location = task.payload.get('location')
            targets = {'S3Targets': [{'Path': location}]}
            crawler = DatasetCrawler(dataset)
            if location:
                crawler.update_crawler(targets)
            return crawler.start_crawler()
