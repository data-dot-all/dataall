from ... import gql
from .resolvers import *

updateKeyValueTags = gql.MutationField(
    name="updateKeyValueTags",
    type=gql.ArrayType(gql.Ref("KeyValueTag")),
    args=[
        gql.Argument(name="input", type=gql.NonNullableType(gql.Ref("UpdateKeyValueTagsInput"))),
    ],
    resolver=update_key_value_tags,
)
