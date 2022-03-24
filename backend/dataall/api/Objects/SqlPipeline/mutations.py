from ... import gql
from .resolvers import *

createSqlPipeline = gql.MutationField(
    name='createSqlPipeline',
    type=gql.Ref('SqlPipeline'),
    args=[
        gql.Argument(
            name='input', type=gql.NonNullableType(gql.Ref('NewSqlPipelineInput'))
        )
    ],
    resolver=create_pipeline,
)

updateSqlPipeline = gql.MutationField(
    name='updateSqlPipeline',
    type=gql.Ref('SqlPipeline'),
    args=[
        gql.Argument(name='sqlPipelineUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='input', type=gql.Ref('UpdateSqlPipelineInput')),
    ],
    resolver=update_pipeline,
)

deleteSqlPipeline = gql.MutationField(
    name='deleteSqlPipeline',
    type=gql.Boolean,
    args=[
        gql.Argument(name='sqlPipelineUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='deleteFromAWS', type=gql.Boolean),
    ],
    resolver=delete_pipeline,
)

startPipeline = gql.MutationField(
    name='startDataProcessingPipeline',
    type=gql.String,
    args=[gql.Argument(name='sqlPipelineUri', type=gql.NonNullableType(gql.String))],
    resolver=start_pipeline,
)
