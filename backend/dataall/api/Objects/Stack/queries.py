from ... import gql
from .resolvers import *

getStack = gql.QueryField(
    name="getStack",
    type=gql.Ref("Stack"),
    args=[
        gql.Argument(name="environmentUri", type=gql.String),
        gql.Argument(name="stackUri", type=gql.NonNullableType(gql.String)),
    ],
    resolver=get_stack,
)

getStackLogs = gql.QueryField(
    name="getStackLogs",
    type=gql.ArrayType(gql.Ref("StackLog")),
    args=[
        gql.Argument(name="environmentUri", type=gql.NonNullableType(gql.String)),
        gql.Argument(name="stackUri", type=gql.NonNullableType(gql.String)),
    ],
    resolver=get_stack_logs,
)
