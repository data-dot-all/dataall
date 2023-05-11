import logging
from botocore.exceptions import ClientError

from dataall.aws.handlers.sts import SessionHelper
from dataall.modules.datasets_base.db.models import Dataset

log = logging.getLogger(__name__)


class DatasetCrawler:
    def __init__(self, dataset: Dataset):
        session = SessionHelper.remote_session(accountid=dataset.AwsAccountId)
        region = dataset.region if dataset.region else 'eu-west-1'
        self._client = session.client('glue', region_name=region)
        self._dataset = dataset

    def get_crawler(self, crawler_name=None):
        crawler = None
        if not crawler_name:
            crawler_name = self._dataset.GlueCrawlerName

        try:
            crawler = self._client.get_crawler(Name=crawler_name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityNotFoundException':
                log.debug(f'Crawler does not exists {crawler_name} %s', e)
            else:
                raise e
        return crawler.get('Crawler') if crawler else None

    def start_crawler(self):
        crawler_name = self._dataset.GlueCrawlerName
        try:
            crawler = self.get_crawler()
            self._client.start_crawler(Name=crawler_name)
            log.info('Crawler %s started ', crawler_name)
            return crawler
        except ClientError as e:
            log.error('Failed to start Crawler due to %s', e)
            raise e

    def update_crawler(self, targets):
        dataset = self._dataset
        crawler_name = dataset.GlueCrawlerName
        try:
            self._client.stop_crawler(Name=crawler_name)
        except ClientError as e:
            if (
                    e.response['Error']['Code'] == 'CrawlerStoppingException'
                    or e.response['Error']['Code'] == 'CrawlerNotRunningException'
            ):
                log.error('Failed to stop crawler %s', e)
        try:
            self._client.update_crawler(
                Name=crawler_name,
                Role=SessionHelper.get_delegation_role_arn(accountid=dataset.AwsAccountId),
                DatabaseName=dataset.GlueDatabaseName,
                Targets=targets,
            )
            log.info('Crawler %s updated ', crawler_name)
        except ClientError as e:
            log.debug('Failed to stop and update crawler %s', e)
            if e.response['Error']['Code'] != 'CrawlerRunningException':
                log.error('Failed to update crawler %s', e)
            else:
                raise e


