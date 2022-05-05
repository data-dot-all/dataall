from ... import gql
from ...constants import DataPipelineRole
from .resolvers import *

SqlPipeline = gql.ObjectType(
    name='SqlPipeline',
    fields=[
        gql.Field('sqlPipelineUri', type=gql.ID),
        gql.Field('name', type=gql.String),
        gql.Field('label', type=gql.String),
        gql.Field('description', type=gql.String),
        gql.Field('tags', type=gql.ArrayType(gql.String)),
        gql.Field('created', type=gql.String),
        gql.Field('updated', type=gql.String),
        gql.Field('owner', type=gql.String),
        gql.Field('repo', type=gql.String),
        gql.Field('SamlGroupName', type=gql.String),
        gql.Field(
            'organization', type=gql.Ref('Organization'), resolver=get_pipeline_org
        ),
        gql.Field(
            'environment', type=gql.Ref('Environment'), resolver=get_pipeline_env
        ),
        gql.Field('cloneUrlHttp', gql.String, resolver=get_clone_url_http),
        gql.Field('stack', gql.Ref('Stack'), resolver=get_stack),
        gql.Field(
            'runs', gql.ArrayType(gql.Ref('SqlPipelineRun')), resolver=get_job_runs
        ),
        gql.Field(
            'builds',
            gql.ArrayType(gql.Ref('SqlPipelineBuild')),
            resolver=get_pipeline_executions,
        ),
        gql.Field(
            'userRoleForPipeline',
            type=DataPipelineRole.toGraphQLEnum(),
            resolver=resolve_user_role,
        ),
    ],
)


SqlPipelineSearchResults = gql.ObjectType(
    name='SqlPipelineSearchResults',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(SqlPipeline)),
    ],
)


SqlPipelineExecution = gql.ObjectType(
    name='SqlPipelineExecution',
    fields=[
        gql.Field(name='executionArn', type=gql.ID),
        gql.Field(name='stateMachineArn', type=gql.NonNullableType(gql.String)),
        gql.Field(name='name', type=gql.NonNullableType(gql.String)),
        gql.Field(name='status', type=gql.NonNullableType(gql.String)),
        gql.Field(name='startDate', type=gql.NonNullableType(gql.String)),
        gql.Field(name='stopDate', type=gql.String),
    ],
)


SqlPipelineExecutionSearchResults = gql.ObjectType(
    name='SqlPipelineExecutionSearchResults',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(SqlPipelineExecution)),
    ],
)

SqlPipelineRun = gql.ObjectType(
    name='SqlPipelineRun',
    fields=[
        gql.Field(name='Id', type=gql.ID),
        gql.Field(name='JobName', type=gql.String),
        gql.Field(name='StartedOn', type=gql.String),
        gql.Field(name='CompletedOn', type=gql.String),
        gql.Field(name='JobRunState', type=gql.String),
        gql.Field(name='ErrorMessage', type=gql.String),
        gql.Field(name='ExecutionTime', type=gql.Integer),
    ],
)


SqlPipelineBuild = gql.ObjectType(
    name='SqlPipelineBuild',
    fields=[
        gql.Field(name='pipelineExecutionId', type=gql.ID),
        gql.Field(name='status', type=gql.String),
        gql.Field(name='startTime', type=gql.String),
        gql.Field(name='lastUpdateTime', type=gql.String),
    ],
)


SqlPipelineBuildSearchResults = gql.ObjectType(
    name='SqlPipelineBuildSearchResults',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(SqlPipelineBuild)),
    ],
)
