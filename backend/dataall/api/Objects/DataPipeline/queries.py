from ... import gql
from .resolvers import *

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


browseDataPipelineRepository = gql.QueryField(
    name='browseDataPipelineRepository',
    args=[
        gql.Argument(
            name='input', type=gql.NonNullableType(gql.Ref('DataPipelineBrowseInput'))
        )
    ],
    resolver=ls,
    type=gql.String,
)

listDataPipelineBranches = gql.QueryField(
    name='listDataPipelineBranches',
    args=[gql.Argument(name='DataPipelineUri', type=gql.NonNullableType(gql.String))],
    resolver=list_branches,
    type=gql.ArrayType(gql.String),
)


getDataPipelineFileContent = gql.QueryField(
    name='getDataPipelineFileContent',
    args=[gql.Argument(name='input', type=gql.Ref('DataPipelineFileContentInput'))],
    resolver=cat,
    type=gql.String,
)

getDataPipelineCredsLinux = gql.QueryField(
    name='getDataPipelineCredsLinux',
    args=[gql.Argument(name='DataPipelineUri', type=gql.NonNullableType(gql.String))],
    type=gql.String,
    resolver=get_creds,
)

