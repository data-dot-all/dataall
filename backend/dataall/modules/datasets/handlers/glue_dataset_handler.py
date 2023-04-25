import logging

from botocore.exceptions import ClientError

from dataall.aws.handlers.service_handlers import Worker
from dataall.aws.handlers.sts import SessionHelper
from dataall.db import models
from dataall.modules.datasets.db.models import Dataset
from dataall.modules.datasets.services.dataset_service import DatasetService

log = logging.getLogger(__name__)


class GlueDatasetHandler:
    @staticmethod
    @Worker.handler(path='glue.dataset.crawler.create')
    def create_crawler(engine, task: models.Task):
        with engine.scoped_session() as session:
            dataset: Dataset = DatasetService.get_dataset_by_uri(
                session, task.targetUri
            )
            location = task.payload.get('location')
            GlueDatasetHandler.create_glue_crawler(
                **{
                    'crawler_name': f'{dataset.GlueDatabaseName}-{location}'[:52],
                    'region': dataset.region,
                    'accountid': dataset.AwsAccountId,
                    'database': dataset.GlueDatabaseName,
                    'location': location or f's3://{dataset.S3BucketName}',
                }
            )

    @staticmethod
    @Worker.handler(path='glue.crawler.start')
    def start_crawler(engine, task: models.Task):
        with engine.scoped_session() as session:
            dataset: Dataset = DatasetService.get_dataset_by_uri(
                session, task.targetUri
            )
            location = task.payload.get('location')
            return GlueDatasetHandler.start_glue_crawler(
                {
                    'crawler_name': dataset.GlueCrawlerName,
                    'region': dataset.region,
                    'accountid': dataset.AwsAccountId,
                    'database': dataset.GlueDatabaseName,
                    'location': location,
                }
            )

    @staticmethod
    def create_glue_crawler(**data):
        try:
            accountid = data['accountid']
            database = data.get('database')
            session = SessionHelper.remote_session(accountid=accountid)
            glue = session.client('glue', region_name=data.get('region', 'eu-west-1'))
            crawler_name = data.get('crawler_name')
            targets = {'S3Targets': [{'Path': data.get('location')}]}
            crawler = GlueDatasetHandler._get_crawler(glue, crawler_name)
            if crawler:
                GlueDatasetHandler._update_existing_crawler(
                    glue, accountid, crawler_name, targets, database
                )
            else:
                crawler = glue.create_crawler(
                    Name=crawler_name,
                    Role=SessionHelper.get_delegation_role_arn(accountid=accountid),
                    DatabaseName=database,
                    Targets=targets,
                    Tags=data.get('tags', {'Application': 'dataall'}),
                )

            glue.start_crawler(Name=crawler_name)
            log.info('Crawler %s started ', crawler_name)
            return crawler
        except ClientError as e:
            log.error('Failed to create Crawler due to %s', e)

    @staticmethod
    def start_glue_crawler(data):
        try:
            accountid = data['accountid']
            crawler_name = data['crawler_name']
            database = data['database']
            targets = {'S3Targets': [{'Path': data.get('location')}]}
            session = SessionHelper.remote_session(accountid=accountid)
            glue = session.client('glue', region_name=data.get('region', 'eu-west-1'))
            if data.get('location'):
                GlueDatasetHandler._update_existing_crawler(
                    glue, accountid, crawler_name, targets, database
                )
            crawler = GlueDatasetHandler._get_crawler(glue, crawler_name)
            glue.start_crawler(Name=crawler_name)
            log.info('Crawler %s started ', crawler_name)
            return crawler
        except ClientError as e:
            log.error('Failed to start Crawler due to %s', e)
            raise e

    @staticmethod
    def _update_existing_crawler(glue, accountid, crawler_name, targets, database):
        try:
            glue.stop_crawler(Name=crawler_name)
        except ClientError as e:
            if (
                    e.response['Error']['Code'] == 'CrawlerStoppingException'
                    or e.response['Error']['Code'] == 'CrawlerNotRunningException'
            ):
                log.error('Failed to stop crawler %s', e)
        try:
            glue.update_crawler(
                Name=crawler_name,
                Role=SessionHelper.get_delegation_role_arn(accountid=accountid),
                DatabaseName=database,
                Targets=targets,
            )
            log.info('Crawler %s updated ', crawler_name)
        except ClientError as e:
            log.debug('Failed to stop and update crawler %s', e)
            if e.response['Error']['Code'] != 'CrawlerRunningException':
                log.error('Failed to update crawler %s', e)
            else:
                raise e

    @staticmethod
    def get_glue_crawler(data):
        try:
            accountid = data['accountid']
            session = SessionHelper.remote_session(accountid=accountid)
            glue = session.client('glue', region_name=data.get('region', 'eu-west-1'))
            crawler_name = data.get('crawler_name')
            crawler = GlueDatasetHandler._get_crawler(glue, crawler_name)
            return crawler
        except ClientError as e:
            log.error('Failed to find Crawler due to %s', e)
            raise e

    @staticmethod
    def _get_crawler(glue, crawler_name):
        crawler = None
        try:
            crawler = glue.get_crawler(Name=crawler_name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityNotFoundException':
                log.debug(f'Crawler does not exists {crawler_name} %s', e)
            else:
                raise e
        return crawler.get('Crawler') if crawler else None