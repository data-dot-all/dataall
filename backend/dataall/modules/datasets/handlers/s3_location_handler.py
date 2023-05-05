import logging

from dataall.aws.handlers.service_handlers import Worker
from dataall.db import models
from dataall.modules.datasets.aws.s3_location_client import S3LocationClient
from dataall.modules.datasets.db.dataset_location_repository import DatasetLocationRepository

log = logging.getLogger(__name__)


class S3DatasetLocationHandler:
    """Handles async requests related to s3 for dataset storage location"""

    @staticmethod
    @Worker.handler(path='s3.prefix.create')
    def create_dataset_location(engine, task: models.Task):
        with engine.scoped_session() as session:
            location = DatasetLocationRepository.get_location_by_uri(
                session, task.targetUri
            )
            S3LocationClient(location).create_bucket_prefix()
            location.locationCreated = True
            return location
