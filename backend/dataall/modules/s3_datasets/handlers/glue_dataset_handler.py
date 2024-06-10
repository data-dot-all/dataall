import logging

from dataall.core.tasks.service_handlers import Worker
from dataall.core.tasks.db.task_models import Task
from dataall.modules.s3_datasets.aws.glue_dataset_client import DatasetCrawler
from dataall.modules.s3_datasets.db.dataset_repositories import DatasetRepository
from dataall.modules.s3_datasets.db.dataset_models import S3Dataset

log = logging.getLogger(__name__)


class DatasetCrawlerHandler:
    @staticmethod
    @Worker.handler(path='glue.crawler.start')
    def start_crawler(engine, task: Task):
        with engine.scoped_session() as session:
            dataset: S3Dataset = DatasetRepository.get_dataset_by_uri(session, task.targetUri)
            location = task.payload.get('location')
            targets = {'S3Targets': [{'Path': location}]}
            crawler = DatasetCrawler(dataset)
            if location:
                crawler.update_crawler(targets)
            return crawler.start_crawler()
