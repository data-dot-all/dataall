from dataall.base.api import gql
from dataall.core.stacks.api.resolvers import get_stack, get_stack_logs, list_key_value_tags

getStack = gql.QueryField(
    name='getStack',
    type=gql.Ref('Stack'),
    args=[
        gql.Argument(name='environmentUri', type=gql.String),
        gql.Argument(name='stackUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='targetUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='targetType', type=gql.NonNullableType(gql.String)),
    ],
    resolver=get_stack,
)

getStackLogs = gql.QueryField(
    name='getStackLogs',
    type=gql.ArrayType(gql.Ref('StackLog')),
    args=[
        gql.Argument(name='targetUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='targetType', type=gql.NonNullableType(gql.String)),
    ],
    resolver=get_stack_logs,
)


listKeyValueTags = gql.QueryField(
    name='listKeyValueTags',
    type=gql.ArrayType(gql.Ref('KeyValueTag')),
    args=[
        gql.Argument(name='targetUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='targetType', type=gql.NonNullableType(gql.String)),
    ],
    resolver=list_key_value_tags,
)
