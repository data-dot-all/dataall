from dataall.base.api import gql

Connection = gql.ObjectType(
    name='Connection',
    fields=[
        gql.Field(name='connectionUri', type=gql.ID),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='connectionType', type=gql.String),
        gql.Field(name='SamlGroupName', type=gql.String),
    ],
)

ConnectionSearchResult = gql.ObjectType(
    name='ConnectionSearchResult',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(Connection)),
    ],
)
