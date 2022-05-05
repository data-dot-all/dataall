import logging

from ... import db
from ...db import models
from .service_handlers import Worker
from .sts import SessionHelper

log = logging.getLogger(__name__)


class S3:
    @staticmethod
    @Worker.handler(path="s3.prefix.create")
    def create_dataset_location(engine, task: models.Task):
        with engine.scoped_session() as session:
            location = db.api.DatasetStorageLocation.get_location_by_uri(session, task.targetUri)
            S3.create_bucket_prefix(location)
            return location

    @staticmethod
    def create_bucket_prefix(location):
        try:
            accountid = location.AWSAccountId
            aws_session = SessionHelper.remote_session(accountid=accountid)
            s3cli = aws_session.client("s3")
            response = s3cli.put_object(Bucket=location.S3BucketName, Body="", Key=location.S3Prefix + "/")
            log.info("Creating S3 Prefix `{}`({}) on AWS #{}".format(location.S3BucketName, accountid, response))
            location.locationCreated = True
        except Exception as e:
            log.error(
                f"Dataset storage location creation failed on S3 for dataset location {location.locationUri} : {e}"
            )
            raise e
