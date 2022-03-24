from ... import gql
from .resolvers import *

listSqlPipelines = gql.QueryField(
    name='listSqlPipelines',
    args=[gql.Argument(name='filter', type=gql.Ref('SqlPipelineFilter'))],
    resolver=list_pipelines,
    type=gql.Ref('SqlPipelineSearchResults'),
)

getSqlPipeline = gql.QueryField(
    name='getSqlPipeline',
    args=[gql.Argument(name='sqlPipelineUri', type=gql.NonNullableType(gql.String))],
    type=gql.Ref('SqlPipeline'),
    resolver=get_pipeline,
)


browseSqlPipelineRepository = gql.QueryField(
    name='browseSqlPipelineRepository',
    args=[
        gql.Argument(
            name='input', type=gql.NonNullableType(gql.Ref('SqlPipelineBrowseInput'))
        )
    ],
    resolver=ls,
    type=gql.String,
)

listSqlPipelineBranches = gql.QueryField(
    name='listSqlPipelineBranches',
    args=[gql.Argument(name='sqlPipelineUri', type=gql.NonNullableType(gql.String))],
    resolver=list_branches,
    type=gql.ArrayType(gql.String),
)


getSqlPipelineFileContent = gql.QueryField(
    name='getSqlPipelineFileContent',
    args=[gql.Argument(name='input', type=gql.Ref('SqlPipelineFileContentInput'))],
    resolver=cat,
    type=gql.String,
)

getSqlPipelineCredsLinux = gql.QueryField(
    name='getSqlPipelineCredsLinux',
    args=[gql.Argument(name='sqlPipelineUri', type=gql.NonNullableType(gql.String))],
    type=gql.String,
    resolver=get_creds,
)


listSqlPipelineExecutions = gql.QueryField(
    name='listSqlPipelineExecutions',
    args=[
        gql.Argument(name='sqlPipelineUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='stage', type=gql.String),
    ],
    resolver=list_pipeline_state_machine_executions,
    type=gql.Ref('SqlPipelineExecutionSearchResults'),
)


listSqlPipelineBuilds = gql.QueryField(
    name='listSqlPipelineBuilds',
    args=[gql.Argument(name='sqlPipelineUri', type=gql.NonNullableType(gql.String))],
    type=gql.Ref('SqlPipelineBuildSearchResults'),
)
