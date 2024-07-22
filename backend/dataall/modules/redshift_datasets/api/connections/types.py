from dataall.base.api import gql

RedshiftConnection = gql.ObjectType(
    name='RedshiftConnection',
    fields=[
        gql.Field(name='connectionUri', type=gql.ID),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='connectionType', type=gql.String),
        gql.Field(name='SamlGroupName', type=gql.String),
        gql.Field(name='label', type=gql.String),
        gql.Field(name='redshiftType', type=gql.String),
        gql.Field(name='clusterId', type=gql.String),
        gql.Field(name='nameSpaceId', type=gql.String),
        gql.Field(name='workgroup', type=gql.String),
        gql.Field(name='database', type=gql.String),
        gql.Field(name='redshiftUser', type=gql.String),
        gql.Field(name='secretArn', type=gql.String),
    ],
)

RedshiftConnectionSearchResult = gql.ObjectType(
    name='RedshiftConnectionSearchResult',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(RedshiftConnection)),
    ],
)

RedshiftTable = gql.ObjectType(
    name='RedshiftTable',
    fields=[gql.Field(name='name', type=gql.String), gql.Field(name='type', type=gql.String)],
)
