import logging

from dataall.modules.notifications.services.notification_service import NotificationService
from dataall.base.api.context import Context
from dataall.base.db import exceptions

log = logging.getLogger(__name__)


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
    return NotificationService.list_my_notifications(filter=filter)


def mark_as_read(
    context: Context,
    source,
    notificationUri: str = None,
):
    _required_uri(notificationUri)
    return NotificationService.mark_as_read(notificationUri=notificationUri)


def count_unread_notifications(context: Context, source):
    return NotificationService.count_unread_notifications()
