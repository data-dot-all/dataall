from ... import gql
from .resolvers import *

markNotificationAsRead = gql.MutationField(
    name='markNotificationAsRead',
    args=[
        gql.Argument(name='notificationUri', type=gql.String),
    ],
    type=gql.Boolean,
    resolver=mark_as_read,
)

deleteNotification = gql.MutationField(
    name='deleteNotification',
    args=[gql.Argument(name='notificationUri', type=gql.String)],
    type=gql.Boolean,
    resolver=delete,
)
