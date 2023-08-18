import logging

from dataall.base.api.context import Context
from dataall.core.notifications.db.notification_repositories import Notification

log = logging.getLogger(__name__)


def list_my_notifications(
    context: Context,
    source,
    filter: dict = None,
):
    with context.engine.scoped_session() as session:
        return Notification.paginated_notifications(
            session=session, username=context.username, filter=filter
        )


def mark_as_read(
    context: Context,
    source,
    notificationUri: str = None,
):
    with context.engine.scoped_session() as session:
        return Notification.read_notification(session, notificationUri)


def count_unread_notifications(context: Context, source):
    with context.engine.scoped_session() as session:
        return Notification.count_unread_notifications(session, context.username)


def count_deleted_notifications(context: Context, source):
    with context.engine.scoped_session() as session:
        return Notification.count_deleted_notifications(
            session, context.username
        )


def count_read_notifications(context: Context, source):
    with context.engine.scoped_session() as session:
        return Notification.count_read_notifications(session, context.username)


def delete(context: Context, source, notificationUri):
    with context.engine.scoped_session() as session:
        return Notification.delete_notification(session, notificationUri)
