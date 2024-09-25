from dataall.base.api import gql

RedshiftConnection = gql.ObjectType(
    name='RedshiftConnection',
    fields=[
        gql.Field('connectionUri', gql.ID),
        gql.Field('name', gql.String),
        gql.Field('connectionType', gql.String),
        gql.Field('SamlGroupName', gql.String),
        gql.Field('label', gql.String),
        gql.Field('redshiftType', gql.String),
        gql.Field('clusterId', gql.String),
        gql.Field('nameSpaceId', gql.String),
        gql.Field('workgroup', gql.String),
        gql.Field('database', gql.String),
        gql.Field('redshiftUser', gql.String),
        gql.Field('secretArn', gql.String),
        gql.Field('encryptionType', gql.String),
    ],
)

RedshiftConnectionSearchResult = gql.ObjectType(
    name='RedshiftConnectionSearchResult',
    fields=[
        gql.Field('count', gql.Integer),
        gql.Field('page', gql.Integer),
        gql.Field('pages', gql.Integer),
        gql.Field('hasNext', gql.Boolean),
        gql.Field('hasPrevious', gql.Boolean),
        gql.Field('nodes', gql.ArrayType(RedshiftConnection)),
    ],
)

RedshiftTable = gql.ObjectType(
    name='RedshiftTable',
    fields=[
        gql.Field('name', gql.String),
        gql.Field('type', gql.String),
        gql.Field('alreadyAdded', gql.String),
    ],
)

ConnectionPermission = gql.ObjectType(
    name='ConnectionPermission',
    fields=[
        gql.Field(name='name', type=gql.String),
        gql.Field(name='description', type=gql.String),
    ],
)

ConnectionGroup = gql.ObjectType(
    name='ConnectionGroup',
    fields=[
        gql.Field(name='groupUri', type=gql.String),
        gql.Field(name='permissions', type=gql.ArrayType(ConnectionPermission)),
    ],
)

ConnectionGroupSearchResult = gql.ObjectType(
    name='ConnectionGroupSearchResult',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(ConnectionGroup)),
    ],
)
