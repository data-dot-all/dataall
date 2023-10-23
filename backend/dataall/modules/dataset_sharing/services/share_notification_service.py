import logging
import enum
from dataall.base.config import config
from dataall.core.tasks.db.task_models import Task
from dataall.core.tasks.service_handlers import Worker
from dataall.modules.dataset_sharing.db.share_object_models import ShareObject
from dataall.modules.datasets_base.db.dataset_models import Dataset
from dataall.base.context import get_context
from dataall.modules.dataset_sharing.db.enums import ShareObjectStatus
from dataall.modules.notifications.db.notification_repositories import NotificationRepository

log = logging.getLogger(__name__)


class DataSharingNotificationType(enum.Enum):
    SHARE_OBJECT_SUBMITTED = 'SHARE_OBJECT_SUBMITTED'
    SHARE_ITEM_REQUEST = 'SHARE_ITEM_REQUEST'
    SHARE_OBJECT_APPROVED = 'SHARE_OBJECT_APPROVED'
    SHARE_OBJECT_REJECTED = 'SHARE_OBJECT_REJECTED'
    SHARE_OBJECT_PENDING_APPROVAL = 'SHARE_OBJECT_PENDING_APPROVAL'
    DATASET_VERSION = 'DATASET_VERSION'


class ShareNotificationService:
    @staticmethod
    def notify_share_object_submission(
            session, username: str, email_id: str, dataset: Dataset, share: ShareObject
    ):
        """Notification sent to:
            - dataset.owner - user
        """
        msg = f'User {username} submitted share request for dataset {dataset.label}'
        subject = f'Data.all | Share Request Submitted for {dataset.label}'

        log.info(f"Creating notification: {dataset.owner}, msg {msg}")

        notifications = [NotificationRepository.create_notification(
            session=session,
            username=dataset.owner,
            notification_type=DataSharingNotificationType.SHARE_OBJECT_SUBMITTED.value,
            target_uri=f'{share.shareUri}|{dataset.datasetUri}',
            message=msg,
        )]
        session.add_all(notifications)

        ShareNotificationService.create_notification_task(session, email_id, dataset, share, subject, msg)
        return notifications

    @staticmethod
    def notify_share_object_approval(
            session, username: str, email_id: str, dataset: Dataset, share: ShareObject
    ):
        """Notification sent to:
            - dataset.SamlAdminGroupName - group
            - dataset.stewards - group
            - dataset.owner - user
            - share.owner - user
        """
        msg = f'User {username} approved share request for dataset {dataset.label}'
        subject = f'Data.all | Share Request Approved for {dataset.label}'

        notifications = []
        targeted_users = ShareNotificationService._get_share_object_targeted_users(
            session, dataset, share
        )
        for user in targeted_users:
            log.info(f"Creating notification: {user}, msg {msg}")
            notifications.append(
                NotificationRepository.create_notification(
                    session=session,
                    username=user,
                    notification_type=DataSharingNotificationType.SHARE_OBJECT_APPROVED.value,
                    target_uri=f'{share.shareUri}|{dataset.datasetUri}',
                    message=msg,
                )
            )
            session.add_all(notifications)

        ShareNotificationService.create_notification_task(session, email_id, dataset, share, subject, msg)

        return notifications

    @staticmethod
    def notify_share_object_rejection(
            session, username: str, email_id: str, dataset: Dataset, share: ShareObject
    ):
        """Notification sent to:
            - dataset.SamlAdminGroupName - group
            - dataset.stewards - group
            - dataset.owner - user
            - share.owner - user
        """
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
                NotificationRepository.create_notification(
                    session=session,
                    username=user,
                    notification_type=DataSharingNotificationType.SHARE_OBJECT_REJECTED.value,
                    target_uri=f'{share.shareUri}|{dataset.datasetUri}',
                    message=msg,
                )
            )
        session.add_all(notifications)

        ShareNotificationService.create_notification_task(session, email_id, dataset, share, subject, msg)

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
                NotificationRepository.create_notification(
                    session=session,
                    username=user,
                    notification_type=DataSharingNotificationType.DATASET_VERSION.value,
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

    @staticmethod
    def create_notification_task(session, email_id, dataset, share, subject, msg):
        """
        Creates SES notification task. Email_id corresponds to the email of the user that triggered the API call.
            - For submitting and requesting email_id = requester email
            - For approving email_id = member of dataset admin or steward team
        """
        share_notification_config = config.get_property('modules.datasets.share_notifications')

        notification_recipient_groups_list = [dataset.SamlAdminGroupName, dataset.stewards]
        notification_recipient_email_ids = []

        if share_notification_config['email']['features']['group_notifications'] == True:
            notification_recipient_groups_list.append(share.groupUri)
        else:
            notification_recipient_email_ids = [email_id]

        for share_notification_config_type in share_notification_config.keys():
            if share_notification_config_type == 'email' and share_notification_config[share_notification_config_type]['active'] == True:

                notification_task: Task = Task(
                    action='notification.service',
                    targetUri=share.shareUri,
                    payload={
                        'notificationType' : share_notification_config_type,
                        'subject': subject,
                        'message': msg,
                        'recipientGroupsList' : notification_recipient_groups_list,
                        'recipientEmailList' : notification_recipient_email_ids
                    },
                )
                session.add(notification_task)
                session.commit()

                Worker.queue(engine=get_context().db_engine, task_ids=[notification_task.taskUri])
            else:
                log.info(f'Notification type : {share_notification_config_type} is not active')
