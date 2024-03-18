"""The module defines GraphQL mutations for the Warehouses"""

from dataall.base.api import gql
from dataall.modules.warehouses.api.input_types import (
    NewWarehouseConnectionInput,
    NewWarehouseConsumerInput,
    ModifyWarehouseConnectionInput,
    ModifyWarehouseConsumerInput,
)
from dataall.modules.warehouses.api.resolvers import (
    create_warehouse_connection,
    create_warehouse_consumer,
    update_warehouse_connection,
    update_warehouse_consumer,
    delete_warehouse_connection,
    delete_warehouse_consumer,
)

createWarehouseConnection = gql.MutationField(
    name='createWarehouseConnection',
    args=[gql.Argument(name='input', type=NewWarehouseConnectionInput)],
    type=gql.Ref('WarehouseConnection'),
    resolver=create_warehouse_connection,
)

createWarehouseConsumer = gql.MutationField(
    name='createWarehouseConsumer',
    args=[gql.Argument(name='input', type=NewWarehouseConsumerInput)],
    type=gql.Ref('WarehouseConsumer'),
    resolver=create_warehouse_consumer,
)

updateWarehouseConnection = gql.MutationField(
    name='updateWarehouseConnection',
    args=[
        gql.Argument(name='connectionUri', type=gql.String),
        gql.Argument(name='input', type=ModifyWarehouseConnectionInput),
    ],
    type=gql.Ref('WarehouseConnection'),
    resolver=update_warehouse_connection,
)

updateWarehouseConsumer = gql.MutationField(
    name='updateWarehouseConsumer',
    args=[
        gql.Argument(name='consumerUri', type=gql.String),
        gql.Argument(name='input', type=ModifyWarehouseConsumerInput),
    ],
    type=gql.Ref('WarehouseConsumer'),
    resolver=update_warehouse_consumer,
)

deleteWarehouseConnection = gql.MutationField(
    name='deleteWarehouseConnection',
    args=[gql.Argument(name='connectionUri', type=gql.NonNullableType(gql.String))],
    resolver=delete_warehouse_connection,
    type=gql.Boolean,
)

deleteWarehouseConsumer = gql.MutationField(
    name='deleteWarehouseConsumer',
    args=[gql.Argument(name='consumerUri', type=gql.NonNullableType(gql.String))],
    resolver=delete_warehouse_consumer,
    type=gql.Boolean,
)
