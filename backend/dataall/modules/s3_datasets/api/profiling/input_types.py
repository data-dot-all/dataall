from dataall.base.api import gql

StartDatasetProfilingRunInput = gql.InputType(
    name='StartDatasetProfilingRunInput',
    arguments=[
        gql.Argument('datasetUri', gql.NonNullableType(gql.String)),
        gql.Argument('GlueTableName', gql.String),
        gql.Argument('tableUri', gql.String),
    ],
)


DatasetProfilingRunFilter = gql.InputType(
    name='DatasetProfilingRunFilter',
    arguments=[
        gql.Argument(name='page', type=gql.Integer),
        gql.Argument(name='pageSize', type=gql.Integer),
        gql.Argument(name='term', type=gql.String),
    ],
)
