from dataall.base.api import gql
from .resolvers import *


listKeyValueTags = gql.QueryField(
    name='listKeyValueTags',
    type=gql.ArrayType(gql.Ref('KeyValueTag')),
    args=[
        gql.Argument(name='targetUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='targetType', type=gql.NonNullableType(gql.String)),
    ],
    resolver=list_key_value_tags,
)
