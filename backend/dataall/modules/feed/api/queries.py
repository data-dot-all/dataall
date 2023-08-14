from dataall.base.api import gql
from dataall.modules.feed.api.resolvers import get_feed


getFeed = gql.QueryField(
    name='getFeed',
    resolver=get_feed,
    args=[
        gql.Argument(name='targetUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='targetType', type=gql.NonNullableType(gql.String)),
    ],
    type=gql.Ref('Feed'),
)
