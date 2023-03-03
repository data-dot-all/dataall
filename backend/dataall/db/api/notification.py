from datetime import datetime

from sqlalchemy import func, and_

from .. import models
from ...db import paginate


class Notification:
    def __init__(self):
        pass

    @staticmethod
    def notify_share_object_submission(
        session, username: str, dataset: models.Dataset, share: models.ShareObject
    ):
        notifications = []
        # stewards = Notification.get_dataset_stewards(session, dataset)
        # for steward in stewards:
        notifications.append(
            Notification.create(
                session=session,
                username=dataset.owner,
                notification_type=models.NotificationType.SHARE_OBJECT_SUBMITTED,
                target_uri=f'{share.shareUri}|{dataset.datasetUri}',
                message=f'User {username} submitted share request for dataset {dataset.label}',
            )
        )
        session.add_all(notifications)
        return notifications

    @staticmethod
    def notify_lftag_share_object_submission(
        session, username: str, lftag: models.LFTag,share: models.LFTagShareObject
    ):
        notifications = []
        notifications.append(
            Notification.create(
                session=session,
                username=lftag.owner,
                notification_type=models.NotificationType.SHARE_OBJECT_SUBMITTED,
                target_uri=f'{share.lftagShareUri}|{lftag.LFTagKey}',
                message=f'User {username} submitted share request for LFTag {lftag.LFTagKey}',
            )
        )
        session.add_all(notifications)
        return notifications

    @staticmethod
    def get_dataset_stewards(session, dataset):
        stewards = list()
        stewards.append(dataset.SamlAdminGroupName)
        stewards.append(dataset.stewards)
        return stewards

    @staticmethod
    def notify_share_object_approval(
        session, username: str, dataset: models.Dataset, share: models.ShareObject
    ):
        notifications = []
        targeted_users = Notification.get_share_object_targeted_users(
            session, dataset, share
        )
        for user in targeted_users:
            notifications.append(
                Notification.create(
                    session=session,
                    username=user,
                    notification_type=models.NotificationType.SHARE_OBJECT_APPROVED,
                    target_uri=f'{share.shareUri}|{dataset.datasetUri}',
                    message=f'User {username} approved share request for dataset {dataset.label}',
                )
            )
            session.add_all(notifications)
        return notifications
    
    @staticmethod
    def notify_lftag_share_object_approval(
        session, username: str, lftag: models.LFTag, share: models.ShareObject
    ):
        notifications = []
        targeted_users = [share.owner, lftag.owner]
        for user in targeted_users:
            notifications.append(
                Notification.create(
                    session=session,
                    username=user,
                    notification_type=models.NotificationType.SHARE_OBJECT_APPROVED,
                    target_uri=f'{share.lftagShareUri}|{lftag.LFTagKey}',
                    message=f'User {username} approved share request for LFTag {lftag.LFTagKey}',
                )
            )
            session.add_all(notifications)
        return notifications

    @staticmethod
    def notify_share_object_rejection(
        session, username: str, dataset: models.Dataset, share: models.ShareObject
    ):
        notifications = []
        targeted_users = Notification.get_share_object_targeted_users(
            session, dataset, share
        )
        for user in targeted_users:
            notifications.append(
                Notification.create(
                    session=session,
                    username=user,
                    notification_type=models.NotificationType.SHARE_OBJECT_REJECTED,
                    target_uri=f'{share.shareUri}|{dataset.datasetUri}',
                    message=f'User {username} approved share request for dataset {dataset.label}',
                )
            )
            session.add_all(notifications)
        return notifications

    @staticmethod
    def notify_lftag_share_object_approval(
        session, username: str, lftag: models.LFTag, share: models.ShareObject
    ):
        notifications = []
        targeted_users = [share.owner, lftag.owner]
        for user in targeted_users:
            notifications.append(
                Notification.create(
                    session=session,
                    username=user,
                    notification_type=models.NotificationType.SHARE_OBJECT_REJECTED,
                    target_uri=f'{share.lftagShareUri}|{lftag.LFTagKey}',
                    message=f'User {username} approved share request for LFTag {lftag.LFTagKey}',
                )
            )
            session.add_all(notifications)
        return notifications

    @staticmethod
    def notify_new_data_available_from_owners(
        session, dataset: models.Dataset, share: models.ShareObject, s3_prefix
    ):
        notifications = []
        targeted_users = Notification.get_share_object_targeted_users(
            session, dataset, share
        )
        for user in targeted_users:
            notifications.append(
                Notification.create(
                    session=session,
                    username=user,
                    notification_type=models.NotificationType.DATASET_VERSION,
                    target_uri=f'{share.shareUri}|{dataset.datasetUri}',
                    message=f'New data (at {s3_prefix}) is available from dataset {dataset.datasetUri} shared by owner {dataset.owner}',
                )
            )
            session.add_all(notifications)
        return notifications

    @staticmethod
    def get_share_object_targeted_users(session, dataset, share):
        targeted_users = Notification.get_dataset_stewards(
            session=session, dataset=dataset
        )
        targeted_users.append(dataset.owner)
        targeted_users.append(share.owner)
        return targeted_users

    @staticmethod
    def create(
        session,
        username,
        notification_type: models.NotificationType,
        target_uri,
        message,
    ) -> models.Notification:
        notification = models.Notification(
            type=notification_type,
            message=message,
            username=username,
            target_uri=target_uri,
        )
        session.add(notification)
        session.commit()
        return notification

    @staticmethod
    def list_my_notifications(session, username):
        return (
            session.query(models.Notification)
            .filter(models.Notification.username == username)
            .order_by(models.Notification.created.desc())
            .all()
        )

    @staticmethod
    def paginated_notifications(session, username, filter=None):
        if not filter:
            filter = {}
        q = session.query(models.Notification).filter(
            models.Notification.username == username
        )
        if filter.get('read'):
            q = q.filter(
                and_(
                    models.Notification.is_read == True,
                    models.Notification.deleted.is_(None),
                )
            )
        if filter.get('unread'):
            q = q.filter(
                and_(
                    models.Notification.is_read == False,
                    models.Notification.deleted.is_(None),
                )
            )
        if filter.get('archived'):
            q = q.filter(models.Notification.deleted.isnot(None))
        return paginate(
            q, page=filter.get('page', 1), page_size=filter.get('pageSize', 20)
        ).to_dict()

    @staticmethod
    def count_unread_notifications(session, username):
        count = (
            session.query(func.count(models.Notification.notificationUri))
            .filter(models.Notification.username == username)
            .filter(models.Notification.is_read == False)
            .filter(models.Notification.deleted.is_(None))
            .scalar()
        )
        return int(count)

    @staticmethod
    def count_read_notifications(session, username):
        count = (
            session.query(func.count(models.Notification.notificationUri))
            .filter(models.Notification.username == username)
            .filter(models.Notification.is_read == True)
            .filter(models.Notification.deleted.is_(None))
            .scalar()
        )
        return int(count)

    @staticmethod
    def count_deleted_notifications(session, username):
        count = (
            session.query(func.count(models.Notification.notificationUri))
            .filter(models.Notification.username == username)
            .filter(models.Notification.deleted.isnot(None))
            .scalar()
        )
        return int(count)

    @staticmethod
    def read_notification(session, notificationUri):
        notification = session.query(models.Notification).get(notificationUri)
        notification.is_read = True
        session.commit()
        return True

    @staticmethod
    def delete_notification(session, notificationUri):
        notification = session.query(models.Notification).get(notificationUri)
        if notification:
            notification.deleted = datetime.now()
            session.commit()
        return True
