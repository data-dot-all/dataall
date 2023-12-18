import logging

from dataall.base.api.context import Context
from dataall.base.context import get_context
from dataall.base.db import exceptions
from dataall.modules.notifications.db.notification_repositories import NotificationRepository

log = logging.getLogger(__name__)

# For simplicity there is no additional layer for the business logic of notifications as it happens with other more
# complex modules. In the resolvers we check the input and we perform the db calls directly.


def _session():
    return get_context().db_engine.scoped_session()


def _required_uri(uri):
    if not uri:
        raise exceptions.RequiredParameter('URI')


def list_my_notifications(
    context: Context,
    source,
    filter: dict = None,
):
    if not filter:
        filter = {}
    with _session() as session:
        return NotificationRepository.paginated_notifications(
            session=session, username=get_context().username, groups=get_context().groups, filter=filter
        )


def mark_as_read(
    context: Context,
    source,
    notificationUri: str = None,
):
    _required_uri(notificationUri)
    with _session() as session:
        return NotificationRepository.read_notification(session=session, notificationUri=notificationUri)


def count_unread_notifications(context: Context, source):
    with _session() as session:
        return NotificationRepository.count_unread_notifications(
            session=session, username=get_context().username, groups=get_context().groups
        )


def count_deleted_notifications(context: Context, source):
    with _session() as session:
        return NotificationRepository.count_deleted_notifications(
            session=session, username=get_context().username, groups=get_context().groups
        )


def count_read_notifications(context: Context, source):
    with _session() as session:
        return NotificationRepository.count_read_notifications(
            session=session, username=get_context().username, groups=get_context().groups
        )


def delete(context: Context, source, notificationUri):
    _required_uri(notificationUri)
    with _session() as session:
        return NotificationRepository.delete_notification(session=session, notificationUri=notificationUri)
