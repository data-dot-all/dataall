from assertpy import assert_that

from integration_tests.errors import GqlError
from integration_tests.modules.notifications.queries import (
    list_notifications,
    count_unread_notifications,
    mark_notification_read,
)


def test_list_notification(client1):
    assert_that(list_notifications(client1)).contains_key('page', 'pages', 'nodes', 'count')
    assert_that(list_notifications(client1, filter={'read': True})).contains_key('page', 'pages', 'nodes', 'count')
    assert_that(list_notifications(client1, filter={'unread': True})).contains_key('page', 'pages', 'nodes', 'count')
    assert_that(list_notifications(client1, filter={'archived': True})).contains_key('page', 'pages', 'nodes', 'count')


def test_count_unread_notification(client1):
    assert_that(count_unread_notifications(client1)).is_greater_than_or_equal_to(0)


def test_read_notification_invalid(client1):
    assert_that(mark_notification_read).raises(GqlError).when_called_with(client1, '').contains(
        'RequiredParameter', 'URI'
    )


def test_read_notification_unauth(client1, client2, persistent_group_share_1):
    count_unread = count_unread_notifications(client1)

    response = list_notifications(client1)
    assert_that(mark_notification_read).raises(GqlError).when_called_with(
        client2, response.nodes[0].notificationUri
    ).contains('UnauthorizedOperation', 'UPDATE NOTIFICATION')

    assert_that(count_unread_notifications(client1)).is_equal_to(count_unread)


def test_read_notification(client1, persistent_group_share_1):
    count_unread = count_unread_notifications(client1)

    response = list_notifications(client1)
    mark_notification_read(client1, response.nodes[0].notificationUri)

    # To Handle Case if the Notification Marked as Read was Already Read Earlier
    assert_that(count_unread_notifications(client1)).is_less_than_or_equal_to(count_unread)
