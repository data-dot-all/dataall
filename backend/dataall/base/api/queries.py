from dataall.base.api import gql
from dataall.base.api.resolvers import enum_resolver
from dataall.base.api.types import EnumResult

enumsQuery = gql.QueryField(
    name='queryEnums',
    args=[gql.Argument(name='enums_names', type=gql.ArrayType(gql.String))],
    type=gql.ArrayType(EnumResult),
    resolver=enum_resolver,
    test_scope='Enums',
)
