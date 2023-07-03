import json
import logging
import os
import sys

from botocore.exceptions import ClientError

from dataall import db
from dataall.aws.handlers.service_handlers import Worker
from dataall.aws.handlers.sts import SessionHelper
from dataall.aws.handlers.sqs import SqsQueue
from dataall.db import get_engine
from dataall.db import models
from dataall.modules.dataset_sharing.db.models import ShareObjectItem
from dataall.modules.dataset_sharing.db.share_object_repository import ShareObjectRepository
from dataall.modules.dataset_sharing.services.share_notification_service import ShareNotificationService
from dataall.modules.datasets.aws.sns_dataset_client import SnsDatasetClient
from dataall.modules.datasets_base.db.dataset_repository import DatasetRepository
from dataall.modules.datasets.tasks.subscriptions import poll_queues
from dataall.utils import json_utils
from dataall.modules.datasets.db.dataset_table_repository import DatasetTableRepository
from dataall.modules.datasets.db.dataset_location_repository import DatasetLocationRepository
from dataall.modules.datasets_base.db.models import DatasetStorageLocation, DatasetTable, Dataset

root = logging.getLogger()
root.setLevel(logging.INFO)
if not root.hasHandlers():
    root.addHandler(logging.StreamHandler(sys.stdout))
log = logging.getLogger(__name__)


class DatasetSubscriptionService:
    def __init__(self, engine):
        self.engine = engine

    @staticmethod
    def get_environments(engine):
        with engine.scoped_session() as session:
            return db.api.Environment.list_all_active_environments(session)

    @staticmethod
    def get_queues(environments: [models.Environment]):
        queues = []
        for env in environments:
            queues.append(
                {
                    'url': f'https://sqs.{env.region}.amazonaws.com/{env.AwsAccountId}/{env.resourcePrefix}-producers-queue-{env.environmentUri}',
                    'region': env.region,
                    'accountid': env.AwsAccountId,
                    'arn': f'arn:aws:sqs:{env.region}:{env.AwsAccountId}:ProducersSubscriptionsQueue-{env.environmentUri}',
                    'name': f'{env.resourcePrefix}-producers-queue-{env.environmentUri}',
                }
            )
        return queues

    def notify_consumers(self, engine, messages):
        log.info(f'Notifying consumers with messages {messages}')

        with engine.scoped_session() as session:
            for message in messages:
                self.publish_table_update_message(session, message)
                self.publish_location_update_message(session, message)

        return True

    def publish_table_update_message(self, session, message):
        table: DatasetTable = DatasetTableRepository.get_table_by_s3_prefix(
            session,
            message.get('prefix'),
            message.get('accountid'),
            message.get('region'),
        )
        if not table:
            log.info(f'No table for message {message}')
        else:
            log.info(
                f'Found table {table.tableUri}|{table.GlueTableName}|{table.S3Prefix}'
            )

            message['table'] = table.GlueTableName
            self._publish_update_message(session, message, table, table)

    def publish_location_update_message(self, session, message):
        location: DatasetStorageLocation = (
            DatasetLocationRepository.get_location_by_s3_prefix(
                session,
                message.get('prefix'),
                message.get('accountid'),
                message.get('region'),
            )
        )
        if not location:
            log.info(f'No location found for message {message}')

        else:
            log.info(f'Found location {location.locationUri}|{location.S3Prefix}')
            self._publish_update_message(session, message, location)

    def _publish_update_message(self, session, message, entity, table: DatasetTable = None):
        dataset: Dataset = DatasetRepository.get_dataset_by_uri(session, entity.datasetUri)

        log.info(
            f'Found dataset {dataset.datasetUri}|{dataset.environmentUri}|{dataset.AwsAccountId}'
        )
        share_items: [ShareObjectItem] = ShareObjectRepository.find_share_items_by_item_uri(session, entity.uri())
        log.info(f'Found shared items for location {share_items}')

        return self.publish_sns_message(
            session, message, dataset, share_items, entity.S3Prefix, table
        )

    def publish_sns_message(
        self, session, message, dataset, share_items, prefix, table: DatasetTable = None
    ):
        for item in share_items:
            share_object = ShareObjectRepository.get_approved_share_object(session, item)
            if not share_object or not share_object.principalId:
                log.error(
                    f'Share Item with no share object or no principalId ? {item.shareItemUri}'
                )
            else:
                environment = session.query(models.Environment).get(
                    share_object.principalId
                )
                if not environment:
                    log.error(
                        f'Environment of share owner was deleted ? {share_object.principalId}'
                    )
                else:
                    log.info(f'Notifying share owner {share_object.owner}')

                    log.info(
                        f'found environment {environment.environmentUri}|{environment.AwsAccountId} of share owner {share_object.owner}'
                    )

                    try:
                        log.info(
                            f'Producer message before notifications: {message}'
                        )

                        self.redshift_copy(
                            session, message, dataset, environment, table
                        )

                        message = {
                            'location': prefix,
                            'owner': dataset.owner,
                            'message': f'Dataset owner {dataset.owner} '
                            f'has updated the table shared with you {prefix}',
                        }

                        sns_client = SnsDatasetClient(environment, dataset)
                        response = sns_client.publish_dataset_message(message)
                        log.info(f'SNS update publish response {response}')

                        notifications = ShareNotificationService.notify_new_data_available_from_owners(
                            session=session,
                            dataset=dataset,
                            share=share_object,
                            s3_prefix=prefix,
                        )
                        log.info(f'Notifications for share owners {notifications}')

                    except ClientError as e:
                        log.error(
                            f'Failed to deliver message {message} due to: {e}'
                        )

    # TODO redshift related code
    def redshift_copy(
        self,
        session,
        message,
        dataset: Dataset,
        environment: models.Environment,
        table: DatasetTable,
    ):
        log.info(
            f'Redshift copy starting '
            f'{environment.environmentUri}|{dataset.datasetUri}'
            f'|{json_utils.to_json(message)}'
        )

        task = models.Task(
            action='redshift.subscriptions.copy',
            targetUri=environment.environmentUri,
            payload={
                'datasetUri': dataset.datasetUri,
                'message': json_utils.to_json(message),
                'tableUri': table.tableUri,
            },
        )
        session.add(task)
        session.commit()

        response = Worker.queue(self.engine, [task.taskUri])
        return response


if __name__ == '__main__':
    ENVNAME = os.environ.get('envname', 'local')
    ENGINE = get_engine(envname=ENVNAME)
    Worker.queue = SqsQueue.send
    log.info('Polling datasets updates...')
    service = DatasetSubscriptionService(ENGINE)
    queues = service.get_queues(service.get_environments(ENGINE))
    messages = poll_queues(queues)
    service.notify_consumers(ENGINE, messages)
    log.info('Datasets updates shared successfully')
