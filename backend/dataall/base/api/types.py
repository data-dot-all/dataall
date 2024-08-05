from dataall.base.api import gql

EnumItem = gql.ObjectType(
    name='EnumItem',
    fields=[
        gql.Field(name='name', type=gql.String),
        gql.Field(name='value', type=gql.String),
    ],
)

EnumResult = gql.ObjectType(
    name='EnumResult',
    fields=[
        gql.Field(name='name', type=gql.String),
        gql.Field(name='items', type=gql.ArrayType(EnumItem)),
    ],
)
