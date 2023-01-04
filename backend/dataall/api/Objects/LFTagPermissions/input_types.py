from ... import gql

LFTagPermissionsFilter = gql.InputType(
    name='LFTagPermissionsFilter',
    arguments=[
        gql.Argument('term', gql.String),
        gql.Argument(name='page', type=gql.Integer),
        gql.Argument(name='pageSize', type=gql.Integer),
    ],
)
