import json
import logging

from botocore.exceptions import ClientError

from ... import db
from ...db import models
from .service_handlers import Worker
from .sts import SessionHelper

logger = logging.getLogger(__name__)


class Sns:
    def __init__(self):
        pass

    @staticmethod
    @Worker.handler(path="sns.dataset.publish_update")
    def publish_update(engine, task: models.Task):
        with engine.scoped_session() as session:
            dataset = db.api.Dataset.get_dataset_by_uri(session, task.targetUri)
            environment = db.api.Environment.get_environment_by_uri(session, dataset.environmentUri)
            aws_session = SessionHelper.remote_session(accountid=environment.AwsAccountId)
            sns = aws_session.client("sns", region_name=environment.region)
            message = {
                "prefix": task.payload["s3Prefix"],
                "accountid": environment.AwsAccountId,
                "region": environment.region,
                "bucket_name": dataset.S3BucketName,
            }
            try:
                logger.info(f"Sending dataset {dataset.datasetUri}|{message} update message for consumers")
                response = sns.publish(
                    TopicArn=f"arn:aws:sns:{environment.region}:{environment.AwsAccountId}:{environment.subscriptionsProducersTopicName}",
                    Message=json.dumps(message),
                )
                return response
            except ClientError as e:
                logger.error(
                    f"Failed to deliver dataset "
                    f"{dataset.datasetUri}|{message} "
                    f"update message for consumers "
                    f"due to: {e} "
                )
                raise e
