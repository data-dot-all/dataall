import json
import logging
import os

from dataall.aws.handlers.service_handlers import Worker
from dataall.db import get_engine

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL'))
log = logging.getLogger(__name__)

ENVNAME = os.getenv('envname', 'local')

engine = get_engine(envname=ENVNAME)


def handler(event, context=None):
    """Processes  messages received from sqs"""
    log.info(f'Received Event: {event}')
    for record in event['Records']:
        log.info('Consumed record from queue: %s' % record)
        message = json.loads(record['body'])
        log.info(f'Extracted Message: {message}')
        Worker.process(engine=engine, task_ids=message)
