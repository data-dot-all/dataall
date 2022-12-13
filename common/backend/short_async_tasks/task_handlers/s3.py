import logging

from backend.short_async_tasks import Worker
from backend.utils.boto3 import SessionHelper, S3
from backend.db.core import operations
from backend.db.common import models

log = logging.getLogger(__name__)


class S3Handler:
    @staticmethod
    @Worker.handler(path='s3.prefix.create')
    def create_dataset_location(engine, task: models.Task):
        with engine.scoped_session() as session:
            location = operations.DatasetStorageLocation.get_location_by_uri(
                session, task.targetUri
            )
            S3.create_bucket_prefix(location)
            return location
