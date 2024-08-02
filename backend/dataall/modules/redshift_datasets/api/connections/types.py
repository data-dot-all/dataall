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
