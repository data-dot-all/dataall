from ... import gql

LFTag = gql.ObjectType(
    name='LFTag',
    fields=[
        gql.Field(name='lftagUri', type=gql.String),
        gql.Field(name='LFTagKey', type=gql.String),
        gql.Field(name='LFTagValues', type=gql.ArrayType(gql.String)),
        gql.Field(name='teams', type=gql.ArrayType(gql.String))
    ],
)

LFTagSearchResult = gql.ObjectType(
    name='LFTagSearchResult',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(LFTag)),
    ],
)
