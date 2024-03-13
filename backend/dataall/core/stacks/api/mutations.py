from dataall.base.api import gql
from dataall.core.stacks.api.resolvers import update_stack, update_key_value_tags


updateStack = gql.MutationField(
    name='updateStack',
    type=gql.Ref('Stack'),
    args=[
        gql.Argument(name='targetUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='targetType', type=gql.NonNullableType(gql.String)),
    ],
    resolver=update_stack,
)


updateKeyValueTags = gql.MutationField(
    name='updateKeyValueTags',
    type=gql.ArrayType(gql.Ref('KeyValueTag')),
    args=[
        gql.Argument(name='input', type=gql.NonNullableType(gql.Ref('UpdateKeyValueTagsInput'))),
    ],
    resolver=update_key_value_tags,
)
