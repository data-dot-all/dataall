from dataall.base.api import gql
from .resolvers import (
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
