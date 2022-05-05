from ... import gql

ActivityFilter = gql.InputType(
    name="ActivityFilter",
    arguments=[
        gql.Argument(name="page", type=gql.Integer),
        gql.Argument(name="pageSize", type=gql.Integer),
    ],
)
