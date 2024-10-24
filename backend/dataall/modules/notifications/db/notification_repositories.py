from datetime import datetime

from sqlalchemy import func, and_, or_

from dataall.modules.notifications.db import notification_models as models
from dataall.base.db import paginate, exceptions
from dataall.base.context import get_context
from functools import wraps


class NotificationAccess:
    @staticmethod
    def is_recipient(f):
        @wraps(f)
        def wrapper(*args, **kwds):
            uri = kwds.get('notificationUri')
            if not uri:
                raise KeyError(f"{f.__name__} doesn't have parameter uri.")
            context = get_context()
            with context.db_engine.scoped_session() as session:
                notification = session.query(models.Notification).get(uri)
                if notification and (notification.recipient in context.groups + [context.username]):
                    return f(*args, **kwds)
                else:
                    raise exceptions.UnauthorizedOperation(
                        action='UPDATE NOTIFICATION',
                        message=f'User {context.username} is not the recipient user/group of the notification {uri}',
                    )

        return wrapper


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
    def count_read_notifications(session, username, groups):
        count = (
            session.query(func.count(models.Notification.notificationUri))
            .filter(or_(models.Notification.recipient == username, models.Notification.recipient.in_(groups)))
            .filter(models.Notification.is_read == True)
            .filter(models.Notification.deleted.is_(None))
            .scalar()
        )
        return int(count)

    @staticmethod
    def count_deleted_notifications(session, username, groups):
        count = (
            session.query(func.count(models.Notification.notificationUri))
            .filter(or_(models.Notification.recipient == username, models.Notification.recipient.in_(groups)))
            .filter(models.Notification.deleted.isnot(None))
            .scalar()
        )
        return int(count)

    @staticmethod
    @NotificationAccess.is_recipient
    def read_notification(session, notificationUri):
        notification = session.query(models.Notification).get(notificationUri)
        notification.is_read = True
        session.commit()
        return True

    @staticmethod
    @NotificationAccess.is_recipient
    def delete_notification(session, notificationUri):
        notification = session.query(models.Notification).get(notificationUri)
        if notification:
            notification.deleted = datetime.now()
            session.commit()
        return True
