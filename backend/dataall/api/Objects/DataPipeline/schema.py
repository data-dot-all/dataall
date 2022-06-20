from ... import gql
from .resolvers import *
from ...constants import DataPipelineRole

DataPipeline = gql.ObjectType(
    name='DataPipeline',
    fields=[
        gql.Field('DataPipelineUri', type=gql.ID),
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
        gql.Field('inputDatasetUri', type=gql.String),
        gql.Field('outputDatasetUri', type=gql.String),
        gql.Field('template', type=gql.String),
        gql.Field('devStages', type=gql.ArrayType(gql.String)),
        gql.Field('devStrategy', type=gql.String),
        gql.Field('cloneUrlHttp', gql.String, resolver=get_clone_url_http),
        gql.Field('stack', gql.Ref('Stack'), resolver=get_stack),
        gql.Field(
            'runs', gql.ArrayType(gql.Ref('DataPipelineRun')), resolver=get_job_runs
        ),
        gql.Field(
            'builds',
            gql.ArrayType(gql.Ref('DataPipelineBuild')),
            resolver=get_pipeline_executions,
        ),
        gql.Field(
            'userRoleForPipeline',
            type=DataPipelineRole.toGraphQLEnum(),
            resolver=resolve_user_role,
        ),
    ],
)


DataPipelineSearchResults = gql.ObjectType(
    name='DataPipelineSearchResults',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(DataPipeline)),
    ],
)


DataPipelineExecution = gql.ObjectType(
    name='DataPipelineExecution',
    fields=[
        gql.Field(name='executionArn', type=gql.ID),
        gql.Field(name='stateMachineArn', type=gql.NonNullableType(gql.String)),
        gql.Field(name='name', type=gql.NonNullableType(gql.String)),
        gql.Field(name='status', type=gql.NonNullableType(gql.String)),
        gql.Field(name='startDate', type=gql.NonNullableType(gql.String)),
        gql.Field(name='stopDate', type=gql.String),
    ],
)


DataPipelineExecutionSearchResults = gql.ObjectType(
    name='DataPipelineExecutionSearchResults',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(DataPipelineExecution)),
    ],
)

DataPipelineRun = gql.ObjectType(
    name='DataPipelineRun',
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


DataPipelineBuild = gql.ObjectType(
    name='DataPipelineBuild',
    fields=[
        gql.Field(name='pipelineExecutionId', type=gql.ID),
        gql.Field(name='status', type=gql.String),
        gql.Field(name='startTime', type=gql.String),
        gql.Field(name='lastUpdateTime', type=gql.String),
    ],
)


DataPipelineBuildSearchResults = gql.ObjectType(
    name='DataPipelineBuildSearchResults',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(DataPipelineBuild)),
    ],
)
