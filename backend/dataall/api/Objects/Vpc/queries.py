from dataall import gql
from .resolvers import *

getNetwork = gql.QueryField(
    name='getNetwork',
    args=[gql.Argument(name='vpcUri', type=gql.NonNullableType(gql.String))],
    type=gql.Ref('Vpc'),
    resolver=get_network,
)
