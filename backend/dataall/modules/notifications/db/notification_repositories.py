from sqlalchemy import func, and_, or_

from dataall.modules.notifications.db import notification_models as models
from dataall.base.db import paginate
from datetime import datetime, timedelta, timezone


class NotificationRepository:
    def __init__(self):
        pass

    @staticmethod
    def create_notification(
        session,
        recipient,
        notification_type,
        target_uri,
        message,
    ) -> models.Notification:
        notification = models.Notification(
            type=notification_type,
            message=message,
            recipient=recipient,
            target_uri=target_uri,
        )
        session.add(notification)
        session.commit()
        return notification

    @staticmethod
    def paginated_notifications(session, username, groups, filter=None):
        q = session.query(models.Notification).filter(
            or_(models.Notification.recipient == username, models.Notification.recipient.in_(groups))
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
            q.order_by(models.Notification.created.desc()),
            page=filter.get('page', 1),
            page_size=filter.get('pageSize', 20),
        ).to_dict()

    @staticmethod
    def count_unread_notifications(session, username, groups):
        count = (
            session.query(func.count(models.Notification.notificationUri))
            .filter(or_(models.Notification.recipient == username, models.Notification.recipient.in_(groups)))
            .filter(models.Notification.is_read == False)
            .filter(models.Notification.deleted.is_(None))
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
    def get_notification(session, uri):
        return session.query(models.Notification).get(uri)

    @staticmethod
    def mark_all_unread_as_read(session, username, groups):
        """Mark all unread notifications as read for a user in a single query"""
        updated_count = (
            session.query(models.Notification)
            .filter(or_(models.Notification.recipient == username, models.Notification.recipient.in_(groups)))
            .filter(models.Notification.is_read == False)
            .filter(models.Notification.deleted.is_(None))
            .update({'is_read': True}, synchronize_session=False)
        )
        session.commit()
        return updated_count

    @staticmethod
    def mark_old_notifications_as_read(session, days_threshold=90):
        """
        Mark unreadnotifications older than days_threshold as read.
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_threshold)

        updated_count = (
            session.query(models.Notification)
            .filter(models.Notification.is_read == False)
            .filter(models.Notification.deleted.is_(None))
            .filter(models.Notification.created < cutoff_date)
            .update({'is_read': True}, synchronize_session=False)
        )

        session.commit()
        return updated_count
