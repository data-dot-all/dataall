"""The module defines GraphQL input types for Omics Runs"""

from dataall.base.api import gql

NewOmicsRunInput = gql.InputType(
    name="NewOmicsRunInput",
    arguments=[
        gql.Field("environmentUri", type=gql.NonNullableType(gql.String)),
        gql.Field("workflowUri", type=gql.NonNullableType(gql.String)),
        gql.Field("label", type=gql.NonNullableType(gql.String)),
        gql.Field("destination", type=gql.String),
        gql.Field("parameterTemplate", type=gql.String),
        gql.Field("SamlAdminGroupName", type=gql.NonNullableType(gql.String)),
    ],
)

# UpdateOmicsRunInput = gql.InputType(
#     name="UpdateOmicsRunInput",
#     arguments=[
#         gql.Argument(name="label", type=gql.String),
#         gql.Argument(name="description", type=gql.String),
#         gql.Argument(name="tags", type=gql.ArrayType(gql.String)),
#         gql.Argument(name="S3InputBucket", type=gql.String),
#         gql.Argument(name="S3InputPrefix", type=gql.String),
#         gql.Argument(name="S3OutputBucket", type=gql.String),
#         gql.Argument(name="S3OutputPrefix", type=gql.String),
#     ],
# )

OmicsFilter = gql.InputType(
    name="OmicsFilter",
    arguments=[
        gql.Argument(name="term", type=gql.String),
        gql.Argument(name="page", type=gql.Integer),
        gql.Argument(name="pageSize", type=gql.Integer),
    ],
)
