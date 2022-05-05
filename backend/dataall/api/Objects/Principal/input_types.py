from ... import gql

PrincipalFilter = gql.InputType(
    name="PrincipalFilter",
    arguments=[
        gql.Argument(name="page", type=gql.Integer),
        gql.Argument(name="pageSize", type=gql.Integer),
        gql.Argument(name="principalType", type=gql.Ref("PrincipalType")),
        gql.Argument(name="term", type=gql.String),
    ],
)
