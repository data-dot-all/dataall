import json
import logging
import os
import sys

import boto3
from botocore.exceptions import ClientError

log = logging.getLogger(__name__)


ENVNAME = os.getenv('envname', 'local')
region = os.getenv('AWS_REGION', 'eu-west-1')


def poll_queues(queues):
    log.debug(f'Received Queues URL: {queues}')

    messages = []

    for queue in queues:
        sqs = boto3.client(
            'sqs', region_name=queue['region'], endpoint_url=f'https://sqs.{queue["region"]}.amazonaws.com'
        )
        try:
            response = sqs.receive_message(
                QueueUrl=queue['url'],
                AttributeNames=['SentTimestamp'],
                MaxNumberOfMessages=10,
                MessageAttributeNames=['All'],
            )

            if not response or not response.get('Messages'):
                log.info(f'No new messages available from queue: {queue["url"]}')

            if response and response.get('Messages'):
                log.info(f'Available messages from queue: {response["Messages"]}')
                for message in response['Messages']:
                    if message.get('Body'):
                        log.info('Consumed message from queue: %s' % message)
                        producer_message = json.loads(json.loads(message.get('Body')).get('Message'))
                        log.info(f'Extracted Message: {producer_message}')

                        messages.append(producer_message)

                        try:
                            log.info(f'Deleting the original message from the Queue: {message}')
                            delete_response = sqs.delete_message(
                                QueueUrl=queue['url'],
                                ReceiptHandle=message.get('ReceiptHandle'),
                            )
                            log.info(f'Deleted message from the Queue response: {delete_response}')
                        except ClientError as e:
                            log.error(f'Failed to delete the original message from queue {queue} due to: {e}')

        except ClientError as e:
            log.error(f'Failed to get messages from queue {queue} due to: {e}')

    return messages
