from ... import gql

Tenant = gql.ObjectType(
    name='Tenant',
    fields=[
        gql.Field(name='tenantUri', type=gql.ID),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='created', type=gql.String),
    ],
)
