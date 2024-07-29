from dataall.base.api import gql

RedshiftRole = gql.ObjectType(
    name='RedshiftRole',
    fields=[
        gql.Field(name='rsRoleUri', type=gql.ID),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='label', type=gql.String),
        gql.Field(name='environmentUri', type=gql.String),
        gql.Field(name='SamlGroupName', type=gql.String),
        gql.Field(
            name='nameSpaceId', type=gql.String
        ),  # TODO: we need to verify that data.all has access to this cluster
    ],
)
