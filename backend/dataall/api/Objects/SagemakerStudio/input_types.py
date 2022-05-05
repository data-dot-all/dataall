from ... import gql

NewSagemakerStudioUserProfileInput = gql.InputType(
    name="NewSagemakerStudioUserProfileInput",
    arguments=[
        gql.Argument("label", gql.NonNullableType(gql.String)),
        gql.Argument("description", gql.String),
        gql.Argument("environmentUri", gql.NonNullableType(gql.String)),
        gql.Argument("tags", gql.ArrayType(gql.String)),
        gql.Argument("topics", gql.String),
        gql.Argument("SamlAdminGroupName", gql.NonNullableType(gql.String)),
    ],
)

ModifySagemakerStudioUserProfileInput = gql.InputType(
    name="ModifySagemakerStudioUserProfileInput",
    arguments=[
        gql.Argument("label", gql.String),
        gql.Argument("tags", gql.ArrayType(gql.String)),
        gql.Argument("description", gql.String),
    ],
)

SagemakerStudioUserProfileFilter = gql.InputType(
    name="SagemakerStudioUserProfileFilter",
    arguments=[
        gql.Argument("term", gql.String),
        gql.Argument("page", gql.Integer),
        gql.Argument("pageSize", gql.Integer),
        gql.Argument("sort", gql.String),
        gql.Argument("limit", gql.Integer),
        gql.Argument("offset", gql.Integer),
    ],
)
