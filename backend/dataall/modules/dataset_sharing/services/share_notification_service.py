import logging
from dataall.base.config import config
from dataall.core.notifications.db.notification_repositories import Notification
from dataall.core.notifications.db.notification_models import NotificationType
from dataall.core.tasks.db.task_models import Task
from dataall.core.tasks.service_handlers import Worker
from dataall.modules.dataset_sharing.db.share_object_models import ShareObject
from dataall.modules.datasets_base.db.dataset_models import Dataset
from dataall.base.context import get_context
from dataall.modules.dataset_sharing.db.enums import ShareObjectStatus, ShareObjectActions

log = logging.getLogger(__name__)


class ShareNotificationService:
    @staticmethod
    def notify_share_object_submission(
            session, username: str, email_id: str, dataset: Dataset, share: ShareObject
    ):
        msg = f'User {username} submitted share request for dataset {dataset.label}'
        subject = f'Data.all | Share Request Submitted for {dataset.label}'

        notifications = [Notification.create(
            session=session,
            username=dataset.owner,
            notification_type=NotificationType.SHARE_OBJECT_SUBMITTED,
            target_uri=f'{share.shareUri}|{dataset.datasetUri}',
            message=msg,
        )]
        session.add_all(notifications)

        create_notification_task(session, email_id, dataset, share, subject, msg)
        return notifications

    @staticmethod
    def notify_share_object_approval(
            session, username: str, email_id: str, dataset: Dataset, share: ShareObject
    ):
        msg = f'User {username} approved share request for dataset {dataset.label}'
        subject = f'Data.all | Share Request Approved for {dataset.label}'

        notifications = []
        targeted_users = ShareNotificationService._get_share_object_targeted_users(
            session, dataset, share
        )
        for user in targeted_users:
            notifications.append(
                Notification.create(
                    session=session,
                    username=user,
                    notification_type=NotificationType.SHARE_OBJECT_APPROVED,
                    target_uri=f'{share.shareUri}|{dataset.datasetUri}',
                    message=msg,
                )
            )
            session.add_all(notifications)

        create_notification_task(session, email_id, dataset, share, subject, msg)

        return notifications

    @staticmethod
    def notify_share_object_rejection(
            session, username: str, email_id: str, dataset: Dataset, share: ShareObject
    ):
        if share.status == ShareObjectStatus.Rejected.value:
            msg = f'User {username} rejected share request for dataset {dataset.label}'
            subject = f'Data.all | Share Request Rejected for {dataset.label}'
        elif share.status == ShareObjectStatus.Revoked.value:
            msg = f'User {username} revoked share request for dataset {dataset.label}'
            subject = f'Data.all | Share Request Revoked for {dataset.label}'
        else:
            msg = f'User {username} rejected / revoked share request for dataset {dataset.label}'
            subject = f'Data.all | Share Request Rejected / Revoked for {dataset.label}'

        notifications = []
        targeted_users = ShareNotificationService._get_share_object_targeted_users(
            session, dataset, share
        )
        for user in targeted_users:
            notifications.append(
                Notification.create(
                    session=session,
                    username=user,
                    notification_type=NotificationType.SHARE_OBJECT_REJECTED,
                    target_uri=f'{share.shareUri}|{dataset.datasetUri}',
                    message=msg,
                )
            )
            session.add_all(notifications)

        create_notification_task(session, email_id, dataset, share, subject, msg)

        return notifications

    @staticmethod
    def notify_new_data_available_from_owners(
            session, dataset: Dataset, share: ShareObject, s3_prefix
    ):
        notifications = []
        targeted_users = ShareNotificationService._get_share_object_targeted_users(
            session, dataset, share
        )
        for user in targeted_users:
            notifications.append(
                Notification.create(
                    session=session,
                    username=user,
                    notification_type=NotificationType.DATASET_VERSION,
                    target_uri=f'{share.shareUri}|{dataset.datasetUri}',
                    message=f'New data (at {s3_prefix}) is available from dataset {dataset.datasetUri} '
                            f'shared by owner {dataset.owner}',
                )
            )
            session.add_all(notifications)
        return notifications

    @staticmethod
    def _get_share_object_targeted_users(session, dataset, share):
        targeted_users = ShareNotificationService._get_dataset_stewards(dataset)
        targeted_users.append(dataset.owner)
        targeted_users.append(share.owner)
        return targeted_users

    @staticmethod
    def _get_dataset_stewards(dataset):
        stewards = list()
        stewards.append(dataset.SamlAdminGroupName)
        stewards.append(dataset.stewards)
        return stewards


def create_notification_task(session, email_id, dataset, share, subject, msg):
    share_notification_config = config.get_property('core.share_notifications')
    requesterGroupName = share.groupUri
    datasetOwnerGroup = dataset.SamlAdminGroupName
    datasetStewardsGroup = dataset.stewards

    for share_notification_config_type in share_notification_config.keys():
        if share_notification_config_type == 'email' and share_notification_config[share_notification_config_type]['active'] == True:

            notification_task: Task = Task(
                action='notification.service',
                targetUri=share.shareUri,
                payload={
                    'notificationType' : share_notification_config_type,
                    'shareRequestUserEmail': email_id,
                    'subject': subject,
                    'message': msg,
                    'requesterGroupName': requesterGroupName,
                    'datasetOwnerGroup': datasetOwnerGroup,
                    'datasetStewardsGroup': datasetStewardsGroup
                },
            )
            session.add(notification_task)
            session.commit()

            Worker.queue(engine=get_context().db_engine, task_ids=[notification_task.taskUri])
        else:
            log.info(f'Notification type : {share_notification_config_type} is not active')
