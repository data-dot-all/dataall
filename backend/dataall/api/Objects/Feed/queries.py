from ... import gql
from .resolvers import *


getFeed = gql.QueryField(
    name="getFeed",
    resolver=get_feed,
    args=[
        gql.Argument(name="targetUri", type=gql.NonNullableType(gql.String)),
        gql.Argument(name="targetType", type=gql.NonNullableType(gql.String)),
    ],
    type=gql.Ref("Feed"),
)
