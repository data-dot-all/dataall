"""The module defines GraphQL input types for Warehouse APIs"""

from dataall.base.api import gql

NewWarehouseConnectionInput = gql.InputType(
    name='NewWarehouseConnectionInput',
    arguments=[
        gql.Argument('label', gql.NonNullableType(gql.String)),
        gql.Argument('description', gql.String),
        gql.Argument('environmentUri', gql.NonNullableType(gql.String)),
        gql.Argument('SamlAdminGroupName', gql.NonNullableType(gql.String)),
    ],
)

NewWarehouseConsumerInput = gql.InputType(
    name='NewWarehouseConsumerInput',
    arguments=[
        gql.Argument('label', gql.NonNullableType(gql.String)),
        gql.Argument('description', gql.String),
        gql.Argument('environmentUri', gql.NonNullableType(gql.String)),
        gql.Argument('SamlAdminGroupName', gql.NonNullableType(gql.String)),
    ],
)

ModifyWarehouseConnectionInput = gql.InputType(
    name='ModifyWarehouseConnectionInput',
    arguments=[],
)

ModifyWarehouseConsumerInput = gql.InputType(
    name='ModifyWarehouseConsumerInput',
    arguments=[],
)

WarehouseFilter = gql.InputType(
    name='WarehouseFilter',
    arguments=[
        gql.Argument('term', gql.String),
        gql.Argument('page', gql.Integer),
        gql.Argument('pageSize', gql.Integer),
    ],
)
