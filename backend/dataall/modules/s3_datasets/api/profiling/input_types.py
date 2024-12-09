from dataall.base.api import gql

StartDatasetProfilingRunInput = gql.InputType(
    name='StartDatasetProfilingRunInput',
    arguments=[
        gql.Argument('datasetUri', gql.NonNullableType(gql.String)),
        gql.Argument('GlueTableName', gql.String),
        gql.Argument('tableUri', gql.String),
    ],
)
