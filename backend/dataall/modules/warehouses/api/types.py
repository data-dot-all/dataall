"""Defines the object types of Warehouses"""

from dataall.base.api import gql


WarehouseConnection = gql.ObjectType(
    name='WarehouseConnection',
    fields=[
        gql.Field(name='connectionUri', type=gql.ID),
        gql.Field(name='name', type=gql.NonNullableType(gql.String)),
        gql.Field(name='warehouseId', type=gql.NonNullableType(gql.String)),
        gql.Field(name='warehouseType', type=gql.NonNullableType(gql.String)),
        gql.Field(name='SamlAdminGroupName', type=gql.NonNullableType(gql.String)),
        gql.Field(name='connectionType', type=gql.NonNullableType(gql.String)),
        gql.Field(name='connectionDetails', type=gql.NonNullableType(gql.String)),
    ],
)


WarehouseConsumer = gql.ObjectType(
    name='WarehouseConsumer',
    fields=[
        gql.Field(name='consumerUri', type=gql.ID),
        gql.Field(name='name', type=gql.NonNullableType(gql.String)),
        gql.Field(name='warehouseId', type=gql.NonNullableType(gql.String)),
        gql.Field(name='warehouseType', type=gql.NonNullableType(gql.String)),
        gql.Field(name='SamlAdminGroupName', type=gql.NonNullableType(gql.String)),
        gql.Field(name='consumerType', type=gql.NonNullableType(gql.String)),
        gql.Field(name='consumerDetails', type=gql.NonNullableType(gql.String)),
    ],
)
