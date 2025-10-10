from sqlalchemy import func, and_, or_

from dataall.modules.notifications.db import notification_models as models
from dataall.base.db import paginate


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
