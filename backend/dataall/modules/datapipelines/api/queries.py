from dataall.base.api import gql
from dataall.modules.datapipelines.api.resolvers import list_pipelines, get_pipeline, get_creds_linux

listDataPipelines = gql.QueryField(
    name='listDataPipelines',
    args=[gql.Argument(name='filter', type=gql.Ref('DataPipelineFilter'))],
    resolver=list_pipelines,
    type=gql.Ref('DataPipelineSearchResults'),
)

getDataPipeline = gql.QueryField(
    name='getDataPipeline',
    args=[gql.Argument(name='DataPipelineUri', type=gql.NonNullableType(gql.String))],
    type=gql.Ref('DataPipeline'),
    resolver=get_pipeline,
)

getDataPipelineCredsLinux = gql.QueryField(
    name='getDataPipelineCredsLinux',
    args=[gql.Argument(name='DataPipelineUri', type=gql.NonNullableType(gql.String))],
    type=gql.String,
    resolver=get_creds_linux,
)
