from ... import gql
from .resolvers import *


FeedTarget = gql.Union(
    name='FeedTarget',
    types=[
        gql.Ref('Dataset'),
        gql.Ref('DatasetTable'),
        gql.Ref('DatasetTableColumn'),
        gql.Ref('DatasetStorageLocation'),
        gql.Ref('DataPipeline'),
        gql.Ref('Worksheet'),
        gql.Ref('Dashboard'),
    ],
    resolver=resolve_feed_target_type,
)

Feed = gql.ObjectType(
    name='Feed',
    fields=[
        gql.Field(name='feedTargetUri', type=gql.NonNullableType(gql.String)),
        gql.Field(name='feedTargetType', type=gql.NonNullableType(gql.String)),
        gql.Field(name='target', resolver=resolve_target, type=gql.Ref('FeedTarget')),
        gql.Field(
            name='messages',
            args=[gql.Argument(name='filter', type=gql.Ref('FeedMessageFilter'))],
            resolver=resolve_messages,
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
