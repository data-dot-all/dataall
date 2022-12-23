from ... import gql

LFTagFilter = gql.InputType(
    name='LFTagFilter',
    arguments=[
        gql.Argument('term', gql.String),
        gql.Argument(name='page', type=gql.Integer),
        gql.Argument(name='pageSize', type=gql.Integer),
    ],
)

AddLFTagInput = gql.InputType(
    name='AddLFTagInput',
    arguments=[
        gql.Argument('LFTagName', gql.NonNullableType(gql.String)),
        gql.Argument('LFTagValues', gql.ArrayType(gql.String))
    ],
)
