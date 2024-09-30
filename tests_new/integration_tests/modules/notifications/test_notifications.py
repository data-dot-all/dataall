from assertpy import assert_that

from integration_tests.errors import GqlError
from integration_tests.modules.notifications.queries import (
    list_notifications,
    count_deleted_notificiations,
    count_read_notificiations,
    count_unread_notificiations,
    mark_notification_read,
    delete_notification,
)


def test_list_notification(client1, session_share_1):
    response = list_notifications(client1)
    assert_that(response).is_not_none()
    assert_that(response.nodes).is_not_empty()
    assert_that(response.nodes[0].notificationUri).is_not_none()

    assert_that(list_notifications(client1, filter={'read': True})).is_not_none()
    assert_that(list_notifications(client1, filter={'unread': True})).is_not_none()
    assert_that(list_notifications(client1, filter={'archived': True})).is_not_none()


def test_count_unread_notification(client1, session_share_1):
    assert_that(count_unread_notificiations(client1)).is_greater_than_or_equal_to(0)


def test_count_read_notification(client1, session_share_1):
    assert_that(count_read_notificiations(client1)).is_greater_than_or_equal_to(0)


def test_read_notification_invalid(client1, session_share_1):
    assert_that(mark_notification_read).raises(GqlError).when_called_with(client1, '').contains(
        'RequiredParameter', 'URI'
    )


def test_read_notification(client1, session_share_1):
    count_unread = count_unread_notificiations(client1)
    count_read = count_read_notificiations(client1)

    response = list_notifications(client1)
    mark_notification_read(client1, response.nodes[0].notificationUri)

    assert_that(count_unread_notificiations(client1)).is_equal_to(count_unread - 1)
    assert_that(count_read_notificiations(client1)).is_equal_to(count_read + 1)


def test_delete_notification_invalid(client1, session_share_1):
    assert_that(delete_notification).raises(GqlError).when_called_with(client1, '').contains('RequiredParameter', 'URI')


def test_delete_notification(client1, session_share_1):
    count_deleted = count_deleted_notificiations(client1)
    response = list_notifications(client1, {'unread': True, 'read': True})
    delete_notification(client1, response.nodes[0].notificationUri)
    assert_that(count_deleted_notificiations(client1)).is_equal_to(count_deleted + 1)
