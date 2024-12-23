"""
A service layer for Notifications
"""

import logging
from dataall.base.db import exceptions

from dataall.base.context import get_context
from dataall.modules.notifications.db import notification_models as models
from functools import wraps

from dataall.modules.notifications.db.notification_repositories import NotificationRepository

logger = logging.getLogger(__name__)


class NotificationAccess:
    @staticmethod
    def check_recipient(uri):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            notification = NotificationRepository.get_notification(session=session, uri=uri)
            return notification and (notification.recipient in context.groups + [context.username])

    @staticmethod
    def is_recipient(f):
        @wraps(f)
        def wrapper(*args, **kwds):
            uri = kwds.get('notificationUri')
            if not uri:
                raise KeyError(f"{f.__name__} doesn't have parameter uri.")

            if NotificationAccess.check_recipient(uri):
                return f(*args, **kwds)
            else:
                raise exceptions.UnauthorizedOperation(
                    action='UPDATE NOTIFICATION',
                    message=f'User {get_context().username} is not the recipient user/group of the notification {uri}',
                )

        return wrapper


class NotificationService:
    """
    Encapsulate the logic of interactions with notifications.
    """

    @staticmethod
    def list_my_notifications(filter: dict = {}):
        """List existed user notifications. Filters only required notifications by the filter param"""
        context = get_context()

        with context.db_engine.scoped_session() as session:
            return NotificationRepository.paginated_notifications(
                session=session, username=context.username, groups=context.groups, filter=filter
            )

    @staticmethod
    @NotificationAccess.is_recipient
    def mark_as_read(notificationUri: str):
        with get_context().db_engine.scoped_session() as session:
            return NotificationRepository.read_notification(session=session, notificationUri=notificationUri)

    @staticmethod
    def count_unread_notifications():
        context = get_context()
        with context.db_engine.scoped_session() as session:
            return NotificationRepository.count_unread_notifications(
                session=session, username=context.username, groups=context.groups
            )
