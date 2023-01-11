from ... import gql

DatasetTableColumnFilter = gql.InputType(
    name='DatasetTableColumnFilter',
    arguments=[
        gql.Argument('term', gql.String),
        gql.Argument('page', gql.Integer),
        gql.Argument('pageSize', gql.Integer),
    ],
)

DatasetTableColumnInput = gql.InputType(
    name='DatasetTableColumnInput',
    arguments=[
        gql.Argument('description', gql.String),
        gql.Argument('classification', gql.Integer),
        gql.Argument('tags', gql.Integer),
        gql.Argument('topics', gql.Integer),
    ],
)

DatasetTableColumnLFTagInput = gql.InputType(
    name='DatasetTableColumnLFTagInput',
    arguments=[
        gql.Argument('lfTagKey', gql.ArrayType(gql.String)),
        gql.Argument('lfTagValue', gql.ArrayType(gql.String))
    ],
)
