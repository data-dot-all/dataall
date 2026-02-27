from dataall.base.api import gql
from .resolvers import mark_as_read, mark_all_as_read


markNotificationAsRead = gql.MutationField(
    name='markNotificationAsRead',
    args=[
        gql.Argument(name='notificationUri', type=gql.String),
    ],
    type=gql.Boolean,
    resolver=mark_as_read,
)

markAllNotificationsAsRead = gql.MutationField(
    name='markAllNotificationsAsRead',
    type=gql.Integer,  # Returns count of notifications marked as read
    resolver=mark_all_as_read,
)
