from ... import gql

NewDataPipelineInput = gql.InputType(
    name='NewDataPipelineInput',
    arguments=[
        gql.Argument(name='label', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='description', type=gql.String),
        gql.Argument(name='SamlGroupName', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='tags', type=gql.ArrayType(gql.String)),
        gql.Argument(name='devStages', type=gql.ArrayType(gql.String)),
        gql.Argument(name='devStrategy', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='inputDatasetUri', type=gql.String),
        gql.Argument(name='outputDatasetUri', type=gql.String),
        gql.Argument(name='template', type=gql.String),
    ],
)


UpdateDataPipelineInput = gql.InputType(
    name='UpdateDataPipelineInput',
    arguments=[
        gql.Argument(name='label', type=gql.String),
        gql.Argument(name='description', type=gql.String),
        gql.Argument(name='tags', type=gql.ArrayType(gql.String)),
    ],
)

DataPipelineFilter = gql.InputType(
    name='DataPipelineFilter',
    arguments=[
        gql.Argument(name='term', type=gql.String),
        gql.Argument(name='page', type=gql.Integer),
        gql.Argument(name='pageSize', type=gql.Integer),
    ],
)

DataPipelineBrowseInput = gql.InputType(
    name='DataPipelineBrowseInput',
    arguments=[
        gql.Argument(name='DataPipelineUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='branch', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='folderPath', type=gql.String),
    ],
)


DataPipelineFileContentInput = gql.InputType(
    name='DataPipelineFileContentInput',
    arguments=[
        gql.Argument(name='DataPipelineUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='branch', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='absolutePath', type=gql.NonNullableType(gql.String)),
    ],
)
