from dataall.base.api import gql
from .resolvers import create_network, delete_network

createNetwork = gql.MutationField(
    name='createNetwork',
    type=gql.Ref('Vpc'),
    args=[gql.Argument(name='input', type=gql.NonNullableType(gql.Ref('NewVpcInput')))],
    resolver=create_network,
)

deleteNetwork = gql.MutationField(
    name='deleteNetwork',
    type=gql.Boolean,
    args=[gql.Argument(name='vpcUri', type=gql.NonNullableType(gql.String))],
    resolver=delete_network,
)
