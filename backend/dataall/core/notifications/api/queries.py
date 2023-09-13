from dataall.base.api import gql
from .resolvers import *


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

countReadNotifications = gql.QueryField(
    name='countReadNotifications',
    type=gql.Integer,
    resolver=count_read_notifications,
)

countDeletedNotifications = gql.QueryField(
    name='countDeletedNotifications',
    type=gql.Integer,
    resolver=count_deleted_notifications,
)
