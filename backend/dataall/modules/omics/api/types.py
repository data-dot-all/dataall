from dataall.base.api import gql
from .resolvers import resolve_omics_workflow, resolve_omics_run_details
from dataall.core.organizations.api.resolvers import resolve_organization_by_env
from dataall.core.environment.api.resolvers import resolve_environment

OmicsWorkflow = gql.ObjectType(
    name='OmicsWorkflow',
    fields=[
        gql.Field(name='workflowUri', type=gql.String),
        gql.Field(name='id', type=gql.String),
        gql.Field(name='arn', type=gql.String),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='label', type=gql.String),
        gql.Field(name='type', type=gql.String),
        gql.Field(name='description', type=gql.String),
        gql.Field(name='parameterTemplate', type=gql.String),
        gql.Field(name='environmentUri', type=gql.String),
    ],
)

OmicsWorkflows = gql.ObjectType(
    name='OmicsWorkflows',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(OmicsWorkflow)),
    ],
)

OmicsRunStatus = gql.ObjectType(
    name='OmicsRunStatus',
    fields=[gql.Field(name='status', type=gql.String), gql.Field(name='statusMessage', type=gql.String)],
)


OmicsRun = gql.ObjectType(
    name='OmicsRun',
    fields=[
        gql.Field('runUri', type=gql.ID),
        gql.Field('environmentUri', type=gql.String),
        gql.Field('organizationUri', type=gql.String),
        gql.Field('name', type=gql.String),
        gql.Field('label', type=gql.String),
        gql.Field('description', type=gql.String),
        gql.Field('tags', type=gql.ArrayType(gql.String)),
        gql.Field('created', type=gql.String),
        gql.Field('updated', type=gql.String),
        gql.Field('owner', type=gql.String),
        gql.Field('workflowUri', type=gql.String),
        gql.Field('SamlAdminGroupName', type=gql.String),
        gql.Field('parameterTemplate', type=gql.String),
        gql.Field('outputDatasetUri', type=gql.String),
        gql.Field('outputUri', type=gql.String),
        gql.Field(
            name='environment',
            type=gql.Ref('Environment'),
            resolver=resolve_environment,
        ),
        gql.Field(
            name='organization',
            type=gql.Ref('Organization'),
            resolver=resolve_organization_by_env,
        ),
        gql.Field(
            name='workflow',
            type=OmicsWorkflow,
            resolver=resolve_omics_workflow,
        ),
        gql.Field(
            name='status',
            type=OmicsRunStatus,
            resolver=resolve_omics_run_details,
        ),
    ],
)


OmicsRunSearchResults = gql.ObjectType(
    name='OmicsRunSearchResults',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(OmicsRun)),
    ],
)
