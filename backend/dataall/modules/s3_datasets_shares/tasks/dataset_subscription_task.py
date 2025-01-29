import logging
import os
import sys

from botocore.exceptions import ClientError

from dataall.core.tasks.service_handlers import Worker
from dataall.base.aws.sqs import SqsQueue
from dataall.core.environment.db.environment_models import Environment
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.base.db import get_engine
from dataall.modules.shares_base.db.share_object_models import ShareObjectItem
from dataall.modules.s3_datasets_shares.db.s3_share_object_repositories import S3ShareObjectRepository
from dataall.modules.shares_base.services.share_notification_service import ShareNotificationService
from dataall.modules.s3_datasets.aws.sns_dataset_client import SnsDatasetClient
from dataall.modules.s3_datasets.db.dataset_location_repositories import DatasetLocationRepository
from dataall.modules.s3_datasets.db.dataset_table_repositories import DatasetTableRepository
from dataall.modules.s3_datasets_shares.tasks.subscriptions import poll_queues
from dataall.modules.s3_datasets.db.dataset_repositories import DatasetRepository
from dataall.modules.s3_datasets.db.dataset_models import DatasetStorageLocation, DatasetTable, S3Dataset
from dataall.modules.datasets_base.db.dataset_models import DatasetBase
from dataall.modules.shares_base.db.share_object_models import ShareObject
from dataall.modules.shares_base.services.share_notification_service import DataSharingNotificationType

log = logging.getLogger(__name__)

# TODO: review this task usage and remove if not needed


class DatasetSubscriptionService:
    def __init__(self, engine):
        self.engine = engine

    @staticmethod
    def get_environments(engine):
        with engine.scoped_session() as session:
            return EnvironmentService.list_all_active_environments(session)

    @staticmethod
    def get_queues(environments: [Environment]):
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
            log.info(f'Found table {table.tableUri}|{table.GlueTableName}|{table.S3Prefix}')

            message['table'] = table.GlueTableName
            self._publish_update_message(session, message, table, table)

    def publish_location_update_message(self, session, message):
        location: DatasetStorageLocation = DatasetLocationRepository.get_location_by_s3_prefix(
            session,
            message.get('prefix'),
            message.get('accountid'),
            message.get('region'),
        )
        if not location:
            log.info(f'No location found for message {message}')

        else:
            log.info(f'Found location {location.locationUri}|{location.S3Prefix}')
            self._publish_update_message(session, message, location)

    def _publish_update_message(self, session, message, entity, table: DatasetTable = None):
        dataset: S3Dataset = DatasetRepository.get_dataset_by_uri(session, entity.datasetUri)

        log.info(f'Found dataset {dataset.datasetUri}|{dataset.environmentUri}|{dataset.AwsAccountId}')
        share_items: [ShareObjectItem] = S3ShareObjectRepository.find_share_items_by_item_uri(session, entity.uri())
        log.info(f'Found shared items for location {share_items}')

        return self.publish_sns_message(session, message, dataset, share_items, entity.S3Prefix, table)

    def publish_sns_message(self, session, message, dataset, share_items, prefix, table: DatasetTable = None):
        for item in share_items:
            share_object = S3ShareObjectRepository.get_approved_share_object(session, item)
            if not share_object or not share_object.principalId:
                log.error(f'Share Item with no share object or no principalId ? {item.shareItemUri}')
            else:
                environment = session.query(Environment).get(share_object.principalId)
                if not environment:
                    log.error(f'Environment of share owner was deleted ? {share_object.principalId}')
                else:
                    log.info(f'Notifying share owner {share_object.owner}')

                    log.info(
                        f'found environment {environment.environmentUri}|{environment.AwsAccountId} of share owner {share_object.owner}'
                    )

                    try:
                        log.info(f'Producer message before notifications: {message}')

                        message = {
                            'location': prefix,
                            'owner': dataset.owner,
                            'message': f'Dataset owner {dataset.owner} has updated the table shared with you {prefix}',
                        }

                        sns_client = SnsDatasetClient(environment, dataset)
                        response = sns_client.publish_dataset_message(message)
                        log.info(f'SNS update publish response {response}')

                        notifications = self.notify_new_data_available_from_owners(
                            session=session, dataset=dataset, share=share_object, s3_prefix=prefix
                        )

                        log.info(f'Notifications for share owners {notifications}')

                    except ClientError as e:
                        log.error(f'Failed to deliver message {message} due to: {e}')

    @staticmethod
    def notify_new_data_available_from_owners(session, dataset: DatasetBase, share: ShareObject, s3_prefix: str):
        msg = (
            f'New data (at {s3_prefix}) is available from dataset {dataset.datasetUri} shared by owner {dataset.owner}'
        )
        notifications = ShareNotificationService(session=session, dataset=dataset, share=share).register_notifications(
            notification_type=DataSharingNotificationType.DATASET_VERSION.value, msg=msg
        )
        return notifications


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
