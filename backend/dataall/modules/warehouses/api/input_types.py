"""The module defines GraphQL input types for Warehouse APIs"""

from dataall.base.api import gql

NewWarehouseConnectionInput = gql.InputType(
    name='NewWarehouseConnectionInput',
    arguments=[
        gql.Argument('name', gql.NonNullableType(gql.String)),
        gql.Argument('environmentUri', gql.NonNullableType(gql.String)),
        gql.Argument('SamlAdminGroupName', gql.NonNullableType(gql.String)),
        gql.Argument('warehouseId', gql.NonNullableType(gql.String)),
        gql.Argument('warehouseType', gql.NonNullableType(gql.String)),
        gql.Argument('databaseName', gql.NonNullableType(gql.String)),
        gql.Argument('authenticationType', gql.NonNullableType(gql.String)),
        gql.Argument('authenticationDetails', gql.NonNullableType(gql.String)),
    ],
)

NewWarehouseConsumerInput = gql.InputType(
    name='NewWarehouseConsumerInput',
    arguments=[
        gql.Argument('name', gql.NonNullableType(gql.String)),
        gql.Argument('environmentUri', gql.NonNullableType(gql.String)),
        gql.Argument('SamlAdminGroupName', gql.NonNullableType(gql.String)),
        gql.Argument('warehouseId', gql.NonNullableType(gql.String)),
        gql.Argument('warehouseType', gql.NonNullableType(gql.String)),
        gql.Argument('consumerType', gql.NonNullableType(gql.String)),
        gql.Argument('consumerDetails', gql.NonNullableType(gql.String)),
    ],
)

ModifyWarehouseConnectionInput = gql.InputType(
    name='ModifyWarehouseConnectionInput',
    arguments=[
        gql.Argument('name', gql.String),
        gql.Argument('SamlAdminGroupName', gql.String),
        gql.Argument('connectionDetails', gql.String),
    ],
)

ModifyWarehouseConsumerInput = gql.InputType(
    name='ModifyWarehouseConsumerInput',
    arguments=[
        gql.Argument('name', gql.String),
        gql.Argument('SamlAdminGroupName', gql.String),
        gql.Argument('consumerDetails', gql.String),
    ],
)

WarehouseFilter = gql.InputType(
    name='WarehouseFilter',
    arguments=[
        gql.Argument('term', gql.String),
        gql.Argument('page', gql.Integer),
        gql.Argument('pageSize', gql.Integer),
    ],
)
