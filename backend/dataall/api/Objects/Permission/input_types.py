from ... import gql

TenantPermissionFilter = gql.InputType(
    name="TenantPermissionFilter",
    arguments=[
        gql.Argument(name="term", type=gql.Boolean),
        gql.Argument(name="page", type=gql.Integer),
        gql.Argument(name="pageSize", type=gql.Integer),
    ],
)

ResourcePermissionFilter = gql.InputType(
    name="ResourcePermissionFilter",
    arguments=[
        gql.Argument(name="term", type=gql.String),
        gql.Argument(name="page", type=gql.Integer),
        gql.Argument(name="pageSize", type=gql.Integer),
    ],
)
