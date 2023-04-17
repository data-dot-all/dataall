import logging

from dataall.aws.handlers.service_handlers import Worker
from dataall.aws.handlers.sts import SessionHelper
from dataall.db import models
from dataall.modules.datasets.services.dataset_location import DatasetStorageLocationService

log = logging.getLogger(__name__)


class S3DatasetLocationHandler:
    """Handles async requests related to s3 for dataset storage location"""

    @staticmethod
    def client(account_id: str, region: str, client_type: str):
        session = SessionHelper.remote_session(accountid=account_id)
        return session.client(client_type, region_name=region)

    @staticmethod
    @Worker.handler(path='s3.prefix.create')
    def create_dataset_location(engine, task: models.Task):
        with engine.scoped_session() as session:
            location = DatasetStorageLocationService.get_location_by_uri(
                session, task.targetUri
            )
            S3DatasetLocationHandler.create_bucket_prefix(location)
            return location

    @staticmethod
    def create_bucket_prefix(location):
        try:
            account_id = location.AWSAccountId
            region = location.region
            s3cli = S3DatasetLocationHandler.client(account_id=account_id, region=region, client_type='s3')
            response = s3cli.put_object(
                Bucket=location.S3BucketName, Body='', Key=location.S3Prefix + '/'
            )
            log.info(
                'Creating S3 Prefix `{}`({}) on AWS #{}'.format(
                    location.S3BucketName, account_id, response
                )
            )
            location.locationCreated = True
        except Exception as e:
            log.error(
                f'Dataset storage location creation failed on S3 for dataset location {location.locationUri} : {e}'
            )
            raise e
