from ... import gql
from .resolvers import get_group

getGroup = gql.QueryField(
    name="getGroup",
    args=[gql.Argument(name="groupUri", type=gql.NonNullableType(gql.String))],
    type=gql.Ref("Group"),
    resolver=get_group,
)
