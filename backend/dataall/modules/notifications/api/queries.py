from dataall.base.api import gql
from .resolvers import (
    count_deleted_notifications,
    count_read_notifications,
    count_unread_notifications,
    list_my_notifications,
)


listNotifications = gql.QueryField(
    name='listNotifications',
    args=[
        gql.Argument(name='filter', type=gql.Ref('NotificationFilter')),
    ],
    type=gql.Ref('NotificationSearchResult'),
    resolver=list_my_notifications,
)

countUnreadNotifications = gql.QueryField(
    name='countUnreadNotifications',
    type=gql.Integer,
    resolver=count_unread_notifications,
)

# Not used in frontend
countReadNotifications = gql.QueryField(
    name='countReadNotifications',
    type=gql.Integer,
    resolver=count_read_notifications,
)

# Not used in frontend
countDeletedNotifications = gql.QueryField(
    name='countDeletedNotifications',
    type=gql.Integer,
    resolver=count_deleted_notifications,
)
