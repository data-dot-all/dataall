from ... import gql
from .resolvers import *


updateKeyValueTags = gql.MutationField(
    name='updateKeyValueTags',
    type=gql.ArrayType(gql.Ref('KeyValueTag')),
    args=[
        gql.Argument(
            name='input', type=gql.NonNullableType(gql.Ref('UpdateKeyValueTagsInput'))
        ),
    ],
    resolver=update_key_value_tags,
)

updateCascadingKeyValueTag = gql.MutationField(
    name='updateCascadingKeyValueTag',
    type=gql.Boolean,
    args=[
        gql.Argument(name='tagUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='targetUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='targetType', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='cascade', type=gql.Boolean),
    ],
    resolver=update_cascading_key_value_tag,
)
