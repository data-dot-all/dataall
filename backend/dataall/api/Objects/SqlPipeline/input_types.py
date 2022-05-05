from ... import gql

NewSqlPipelineInput = gql.InputType(
    name="NewSqlPipelineInput",
    arguments=[
        gql.Argument(name="label", type=gql.NonNullableType(gql.String)),
        gql.Argument(name="environmentUri", type=gql.NonNullableType(gql.String)),
        gql.Argument(name="description", type=gql.String),
        gql.Argument(name="SamlGroupName", type=gql.NonNullableType(gql.String)),
        gql.Argument(name="tags", type=gql.ArrayType(gql.String)),
    ],
)


UpdateSqlPipelineInput = gql.InputType(
    name="UpdateSqlPipelineInput",
    arguments=[
        gql.Argument(name="label", type=gql.String),
        gql.Argument(name="description", type=gql.String),
        gql.Argument(name="tags", type=gql.ArrayType(gql.String)),
    ],
)

SqlPipelineFilter = gql.InputType(
    name="SqlPipelineFilter",
    arguments=[
        gql.Argument(name="term", type=gql.String),
        gql.Argument(name="page", type=gql.Integer),
        gql.Argument(name="pageSize", type=gql.Integer),
    ],
)

SqlPipelineBrowseInput = gql.InputType(
    name="SqlPipelineBrowseInput",
    arguments=[
        gql.Argument(name="sqlPipelineUri", type=gql.NonNullableType(gql.String)),
        gql.Argument(name="branch", type=gql.NonNullableType(gql.String)),
        gql.Argument(name="folderPath", type=gql.String),
    ],
)


SqlPipelineFileContentInput = gql.InputType(
    name="SqlPipelineFileContentInput",
    arguments=[
        gql.Argument(name="sqlPipelineUri", type=gql.NonNullableType(gql.String)),
        gql.Argument(name="branch", type=gql.NonNullableType(gql.String)),
        gql.Argument(name="absolutePath", type=gql.NonNullableType(gql.String)),
    ],
)
