import json
import logging

from botocore.exceptions import ClientError

from dataall.base.aws.sts import SessionHelper
from dataall.core.environment.db.environment_models import Environment
from dataall.modules.s3_datasets.db.dataset_models import S3Dataset

log = logging.getLogger(__name__)


class SnsDatasetClient:
    def __init__(self, environment: Environment, dataset: S3Dataset):
        aws_session = SessionHelper.remote_session(accountid=environment.AwsAccountId, region=environment.region)

        self._client = aws_session.client('sns', region_name=environment.region)
        self._topic = (
            f'arn:aws:sns:{environment.region}:{environment.AwsAccountId}:{environment.subscriptionsConsumersTopicName}'
        )
        self._dataset = dataset

    def publish_dataset_message(self, message: dict):
        try:
            response = self._client.publish(
                TopicArn=self._topic,
                Message=json.dumps(message),
            )
            return response
        except ClientError as e:
            log.error(
                f'Failed to deliver dataset '
                f'{self._dataset.datasetUri}|{message} '
                f'update message for consumers '
                f'due to: {e} '
            )
            raise e
