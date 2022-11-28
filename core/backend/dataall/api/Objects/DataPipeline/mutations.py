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

createDataPipelineEnvironment = gql.MutationField(
    name='createDataPipelineEnvironment',
    type=gql.Ref('DataPipelineEnvironment'),
    args=[
        gql.Argument(
            name='input', type=gql.NonNullableType(gql.Ref('NewDataPipelineEnvironmentInput'))
        )
    ],
    resolver=create_pipeline_environment,
)
