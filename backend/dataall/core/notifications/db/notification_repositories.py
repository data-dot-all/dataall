from datetime import datetime

from sqlalchemy import func, and_

from dataall.core.notifications.db import notification_models as models
from dataall.base.db import paginate


class Notification:
    def __init__(self):
        pass

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
