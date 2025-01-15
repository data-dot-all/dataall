from dataall.base.api import gql
from .resolvers import mark_as_read


markNotificationAsRead = gql.MutationField(
    name='markNotificationAsRead',
    args=[
        gql.Argument(name='notificationUri', type=gql.String),
    ],
    type=gql.Boolean,
    resolver=mark_as_read,
)
