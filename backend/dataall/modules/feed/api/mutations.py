from dataall.base.api import gql
from dataall.modules.feed.api.resolvers import post_feed_message


postFeedMessage = gql.MutationField(
    name='postFeedMessage',
    resolver=post_feed_message,
    args=[
        gql.Argument(name='targetUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='targetType', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='input', type=gql.Ref('FeedMessageInput')),
    ],
    type=gql.Ref('FeedMessage'),
)
