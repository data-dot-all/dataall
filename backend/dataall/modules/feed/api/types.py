from dataall.base.api import gql
from dataall.modules.feed.api.resolvers import resolve_feed_target_type, resolve_feed_messages
from dataall.modules.feed.api.registry import FeedRegistry


FeedTarget = gql.Union(
    name='FeedTarget',
    type_registry=FeedRegistry,
    resolver=resolve_feed_target_type,
)

Feed = gql.ObjectType(
    name='Feed',
    fields=[
        gql.Field(name='feedTargetUri', type=gql.NonNullableType(gql.String)),
        gql.Field(name='feedTargetType', type=gql.NonNullableType(gql.String)),
        gql.Field(
            name='messages',
            args=[gql.Argument(name='filter', type=gql.Ref('FeedMessageFilter'))],
            resolver=resolve_feed_messages,
            type=gql.Ref('FeedMessages'),
        ),
    ],
)


FeedMessage = gql.ObjectType(
    name='FeedMessage',
    fields=[
        gql.Field(name='feedMessageUri', type=gql.ID),
        gql.Field(name='creator', type=gql.NonNullableType(gql.String)),
        gql.Field(name='content', type=gql.String),
        gql.Field(name='created', type=gql.String),
    ],
)


FeedMessages = gql.ObjectType(
    name='FeedMessages',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(gql.Ref('FeedMessage'))),
    ],
)
