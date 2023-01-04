from ... import gql

LFTagPermission = gql.ObjectType(
    name='LFTagPermission',
    fields=[
        gql.Field(name='tagPermissionUri', type=gql.String),
        gql.Field(name='SamlGroupName', type=gql.String),
        gql.Field(name='environmentUri', type=gql.String),
        gql.Field(name='awsAccount', type=gql.String),
        gql.Field(name='tagKey', type=gql.String),
        gql.Field(name='tagValues', type=gql.ArrayType(gql.String))
    ],
)

LFTagPermissionSearchResult = gql.ObjectType(
    name='LFTagPermissionSearchResult',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(LFTagPermission)),
    ],
)
