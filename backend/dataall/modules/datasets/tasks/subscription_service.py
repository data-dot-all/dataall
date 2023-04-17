import json
import logging
import os
import sys

from botocore.exceptions import ClientError
from sqlalchemy import and_

from dataall import db
from dataall.aws.handlers.service_handlers import Worker
from dataall.aws.handlers.sts import SessionHelper
from dataall.aws.handlers.sqs import SqsQueue
from dataall.db import get_engine
from dataall.db import models
from dataall.modules.datasets.services.dataset_profiling_service import DatasetProfilingService
from dataall.tasks.subscriptions import poll_queues
from dataall.utils import json_utils
from dataall.modules.datasets.services.dataset_table import DatasetTableService
from dataall.modules.datasets.services.dataset_location import DatasetStorageLocationService
from dataall.modules.datasets.db.models import DatasetStorageLocation

root = logging.getLogger()
root.setLevel(logging.INFO)
if not root.hasHandlers():
    root.addHandler(logging.StreamHandler(sys.stdout))
log = logging.getLogger(__name__)


class SubscriptionService:
    def __init__(self):
        pass

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

    @staticmethod
    def notify_consumers(engine, messages):

        log.info(f'Notifying consumers with messages {messages}')

        with engine.scoped_session() as session:

            for message in messages:

                SubscriptionService.publish_table_update_message(engine, message)

                SubscriptionService.publish_location_update_message(session, message)

        return True

    @staticmethod
    def publish_table_update_message(engine, message):
        with engine.scoped_session() as session:
            table: models.DatasetTable = DatasetTableService.get_table_by_s3_prefix(
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

                dataset: models.Dataset = session.query(models.Dataset).get(
                    table.datasetUri
                )
                log.info(
                    f'Found dataset {dataset.datasetUri}|{dataset.environmentUri}|{dataset.AwsAccountId}'
                )
                share_items: [models.ShareObjectItem] = (
                    session.query(models.ShareObjectItem)
                    .filter(models.ShareObjectItem.itemUri == table.tableUri)
                    .all()
                )
                log.info(f'Found shared items for table {share_items}')

                return SubscriptionService.publish_sns_message(
                    engine,
                    message,
                    dataset,
                    share_items,
                    table.S3Prefix,
                    table=table,
                )

    @staticmethod
    def publish_location_update_message(session, message):
        location: DatasetStorageLocation = (
            DatasetStorageLocationService.get_location_by_s3_prefix(
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

            dataset: models.Dataset = session.query(models.Dataset).get(
                location.datasetUri
            )
            log.info(
                f'Found dataset {dataset.datasetUri}|{dataset.environmentUri}|{dataset.AwsAccountId}'
            )
            share_items: [models.ShareObjectItem] = (
                session.query(models.ShareObjectItem)
                .filter(models.ShareObjectItem.itemUri == location.locationUri)
                .all()
            )
            log.info(f'Found shared items for location {share_items}')

            return SubscriptionService.publish_sns_message(
                session, message, dataset, share_items, location.S3Prefix
            )

    @staticmethod
    def store_dataquality_results(session, message):

        table: models.DatasetTable = DatasetTableService.get_table_by_s3_prefix(
            session,
            message.get('prefix'),
            message.get('accountid'),
            message.get('region'),
        )

        run = DatasetProfilingService.start_profiling(
            session=session,
            datasetUri=table.datasetUri,
            GlueTableName=table.GlueTableName,
            tableUri=table.tableUri,
        )

        run.status = 'SUCCEEDED'
        run.GlueTableName = table.GlueTableName
        quality_results = message.get('dataQuality')

        if message.get('datasetRegionId'):
            quality_results['regionId'] = message.get('datasetRegionId')

        if message.get('rows'):
            quality_results['table_nb_rows'] = message.get('rows')

        SubscriptionService.set_columns_type(quality_results, message)

        data_types = SubscriptionService.set_data_types(message)

        quality_results['dataTypes'] = data_types

        quality_results['integrationDateTime'] = message.get('integrationDateTime')

        results = json.dumps(json_utils.to_json(quality_results))

        log.info(
            '>>> Stored dataQuality results received from the SNS notification: %s',
            results,
        )

        run.results = results

        session.commit()
        return True

    @staticmethod
    def set_data_types(message):
        data_types = []
        for field in message.get('fields'):
            added = False
            for d in data_types:
                if d.get('type').lower() == field[1].lower():
                    d['count'] = d['count'] + 1
                    added = True
                    break
            if not added:
                data_types.append({'type': field[1], 'count': 1})
        return data_types

    @staticmethod
    def set_columns_type(quality_results, message):
        for c in quality_results.get('columns'):
            if not c.get('Type'):
                for field in message.get('fields'):
                    if field[0].lower() == c['Name'].lower():
                        c['Type'] = field[1]

    @staticmethod
    def publish_sns_message(
        engine, message, dataset, share_items, prefix, table: models.DatasetTable = None
    ):
        with engine.scoped_session() as session:
            for item in share_items:

                share_object = SubscriptionService.get_approved_share_object(
                    session, item
                )

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

                            if table:
                                message['table'] = table.GlueTableName

                            log.info(
                                f'Producer message before notifications: {message}'
                            )

                            SubscriptionService.redshift_copy(
                                engine, message, dataset, environment, table
                            )

                            message = {
                                'location': prefix,
                                'owner': dataset.owner,
                                'message': f'Dataset owner {dataset.owner} '
                                f'has updated the table shared with you {prefix}',
                            }

                            response = SubscriptionService.sns_call(
                                message, environment
                            )

                            log.info(f'SNS update publish response {response}')

                            notifications = db.api.Notification.notify_new_data_available_from_owners(
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

    @staticmethod
    def sns_call(message, environment):
        aws_session = SessionHelper.remote_session(environment.AwsAccountId)
        sns = aws_session.client('sns', region_name=environment.region)
        response = sns.publish(
            TopicArn=f'arn:aws:sns:{environment.region}:{environment.AwsAccountId}:{environment.subscriptionsConsumersTopicName}',
            Message=json.dumps(message),
        )
        return response

    @staticmethod
    def redshift_copy(
        engine,
        message,
        dataset: models.Dataset,
        environment: models.Environment,
        table: models.DatasetTable,
    ):
        log.info(
            f'Redshift copy starting '
            f'{environment.environmentUri}|{dataset.datasetUri}'
            f'|{json_utils.to_json(message)}'
        )
        with engine.scoped_session() as session:
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

        response = Worker.queue(engine, [task.taskUri])
        return response

    @staticmethod
    def get_approved_share_object(session, item):
        share_object: models.ShareObject = (
            session.query(models.ShareObject)
            .filter(
                and_(
                    models.ShareObject.shareUri == item.shareUri,
                    models.ShareObject.status == 'Approved',
                )
            )
            .first()
        )
        return share_object


if __name__ == '__main__':
    ENVNAME = os.environ.get('envname', 'local')
    ENGINE = get_engine(envname=ENVNAME)
    Worker.queue = SqsQueue.send
    log.info('Polling datasets updates...')
    service = SubscriptionService()
    queues = service.get_queues(service.get_environments(ENGINE))
    messages = poll_queues(queues)
    service.notify_consumers(ENGINE, messages)
    log.info('Datasets updates shared successfully')
