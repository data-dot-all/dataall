from dataall import gql
from .resolvers import *


updateStack = gql.MutationField(
    name='updateStack',
    type=gql.Ref('Stack'),
    args=[
        gql.Argument(name='targetUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='targetType', type=gql.NonNullableType(gql.String)),
    ],
    resolver=update_stack,
)
