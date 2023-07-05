from dataall import gql
from .resolvers import *


postFeedMessage = gql.MutationField(
    name='postFeedMessage',
    resolver=post_message,
    args=[
        gql.Argument(name='targetUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='targetType', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='input', type=gql.Ref('FeedMessageInput')),
    ],
    type=gql.Ref('FeedMessage'),
)
