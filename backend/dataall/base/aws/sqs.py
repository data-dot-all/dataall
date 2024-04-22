import json
import logging
import os
import uuid

import boto3
from botocore.exceptions import ClientError

from dataall.base.utils import Parameter

logger = logging.getLogger(__name__)


class SqsQueue:
    disabled = True
    queue_url = None

    @classmethod
    def configure_(cls, queue_url):
        if queue_url:
            cls.enable()
            cls.queue_url = queue_url
        else:
            cls.disable()

    @classmethod
    def disable(cls):
        cls.disabled = True

    @classmethod
    def enable(cls):
        cls.disabled = False

    @classmethod
    def get_envname(cls):
        return os.environ.get('envname', 'local')

    @classmethod
    def get_sqs_client(cls):
        if not cls.disabled:
            client = boto3.client('sqs', region_name=os.getenv('AWS_REGION', 'eu-west-1'))
            return client

    @classmethod
    def send(cls, engine, task_ids: [str]):
        cls.configure_(Parameter().get_parameter(env=cls.get_envname(), path='sqs/queue_url'))
        client = cls.get_sqs_client()
        logger.debug(f'Sending task {task_ids} through SQS {cls.queue_url}')
        try:
            return client.send_message(
                QueueUrl=cls.queue_url,
                MessageBody=json.dumps(task_ids),
                MessageGroupId=cls._get_random_message_id(),
                MessageDeduplicationId=cls._get_random_message_id(),
            )
        except ClientError as e:
            logger.error(e)
            raise e

    @classmethod
    def _get_random_message_id(cls):
        return str(uuid.uuid4())
