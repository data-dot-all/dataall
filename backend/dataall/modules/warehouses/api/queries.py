"""The module defines GraphQL queries for Warehouses"""

from dataall.base.api import gql
from dataall.modules.warehouses.api.resolvers import list_warehouse_connections, list_warehouse_consumers

listWarehouseConnections = gql.QueryField(
    name='listWarehouseConnections',
    args=[gql.Argument(name='filter', type=gql.Ref('WarehouseFilter'))],
    type=gql.Ref('WarehouseConnection'),
    resolver=list_warehouse_connections,
)

listWarehouseConsumers = gql.QueryField(
    name='listWarehouseConsumers',
    args=[gql.Argument(name='filter', type=gql.Ref('WarehouseFilter'))],
    type=gql.Ref('WarehouseConnection'),
    resolver=list_warehouse_consumers,
)
