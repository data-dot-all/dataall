from ... import gql
from .resolvers import *

createDataPipeline = gql.MutationField(
    name='createDataPipeline',
    type=gql.Ref('DataPipeline'),
    args=[
        gql.Argument(
            name='input', type=gql.NonNullableType(gql.Ref('NewDataPipelineInput'))
        )
    ],
    resolver=create_pipeline,
)

updateDataPipeline = gql.MutationField(
    name='updateDataPipeline',
    type=gql.Ref('DataPipeline'),
    args=[
        gql.Argument(name='DataPipelineUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='input', type=gql.Ref('UpdateDataPipelineInput')),
    ],
    resolver=update_pipeline,
)

deleteDataPipeline = gql.MutationField(
    name='deleteDataPipeline',
    type=gql.Boolean,
    args=[
        gql.Argument(name='DataPipelineUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='deleteFromAWS', type=gql.Boolean),
    ],
    resolver=delete_pipeline,
)

startPipeline = gql.MutationField(
    name='startDataProcessingPipeline',
    type=gql.String,
    args=[gql.Argument(name='DataPipelineUri', type=gql.NonNullableType(gql.String))],
    resolver=start_pipeline,
)
