import logging
import os

import boto3

logger = logging.getLogger(__name__)


class EventBridge:

    def __init__(self):
        self.client = boto3.client('events', region_name=os.getenv('AWS_REGION', 'eu-west-1'))

    def enable_scheduled_ecs_tasks(self, list_of_tasks):
        logger.info("Enabling ecs tasks")
        try:
            for ecs_task in list_of_tasks:
                self.client.enable_rule(Name=ecs_task)
        except Exception as e:
            logger.error(f'Error while re-enabling scheduled ecs tasks due to {e}')
            raise e

    def disable_scheduled_ecs_tasks(self, list_of_tasks):
        logger.info("Disabling ecs tasks")
        try:
            for ecs_task in list_of_tasks:
                self.client.disable_rule(Name=ecs_task)
        except Exception as e:
            logger.error(f'Error while re-enabling scheduled ecs tasks due to {e}')
            raise e