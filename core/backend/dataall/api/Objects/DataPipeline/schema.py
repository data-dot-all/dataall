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
        gql.Field(
            'developmentEnvironments',
            type=gql.Ref('DataPipelineEnvironmentSearchResults'),
            resolver=list_pipeline_environments,
        ),
        gql.Field('template', type=gql.String),
        gql.Field('devStrategy', type=gql.String),
        gql.Field('cloneUrlHttp', gql.String, resolver=get_clone_url_http),
        gql.Field('stack', gql.Ref('Stack'), resolver=get_stack),
        gql.Field('cicdStack', gql.Ref('Stack'), resolver=get_cicd_stack),
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


DataPipelineEnvironment = gql.ObjectType(
    name='DataPipelineEnvironment',
    fields=[
        gql.Field(name='envPipelineUri', type=gql.String),
        gql.Field(name='environmentUri', type=gql.String),
        gql.Field(name='environmentLabel', type=gql.String),
        gql.Field(name='pipelineUri', type=gql.String),
        gql.Field(name='pipelineLabel', type=gql.String),
        gql.Field(name='stage', type=gql.String),
        gql.Field(name='order', type=gql.Integer),
        gql.Field(name='region', type=gql.String),
        gql.Field(name='AwsAccountId', type=gql.String),
        gql.Field(name='samlGroupName', type=gql.String),
    ],
)


DataPipelineEnvironmentSearchResults = gql.ObjectType(
    name='DataPipelineEnvironmentSearchResults',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(DataPipelineEnvironment)),
    ],
)
