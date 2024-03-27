from dataall.base.api import gql
from dataall.modules.datasets_base.services.datasets_base_enums import DatasetRole
from dataall.modules.datasets_base.api.resolvers import (
    get_dataset_environment,
    get_dataset_organization,
    get_dataset_owners_group,
    get_dataset_stewards_group,
    #resolve_user_role, #TODO: decide whether we want to include it
    get_dataset_glossary_terms,
    get_dataset_stack,
)
from dataall.core.environment.api.enums import EnvironmentPermission


Dataset = gql.ObjectType(
    name='Dataset',
    fields=[
        gql.Field(name='datasetUri', type=gql.ID),
        gql.Field(name='label', type=gql.String),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='description', type=gql.String),
        gql.Field(name='tags', type=gql.ArrayType(gql.String)),
        gql.Field(name='owner', type=gql.String),
        gql.Field(name='created', type=gql.String),
        gql.Field(name='updated', type=gql.String),
        gql.Field(name='admins', type=gql.ArrayType(gql.String)),
        gql.Field(name='AwsAccountId', type=gql.String),
        gql.Field(name='region', type=gql.String),
        gql.Field(name='SamlAdminGroupName', type=gql.String),
        gql.Field(name='businessOwnerEmail', type=gql.String),
        gql.Field(name='businessOwnerDelegationEmails', type=gql.ArrayType(gql.String)),
        gql.Field(
            name='environment',
            type=gql.Ref('Environment'),
            resolver=get_dataset_environment,
        ),
        gql.Field(
            name='organization',
            type=gql.Ref('Organization'),
            resolver=get_dataset_organization,
        ),
        gql.Field(
            name='owners',
            type=gql.String,
            resolver=get_dataset_owners_group,
        ),
        gql.Field(
            name='stewards',
            type=gql.String,
            resolver=get_dataset_stewards_group,
        ),
        # gql.Field(
        #     name='userRoleForDataset',
        #     type=DatasetRole.toGraphQLEnum(),
        #     resolver=resolve_user_role,
        # ),
        gql.Field(name='userRoleInEnvironment', type=EnvironmentPermission.toGraphQLEnum()),
        gql.Field(
            name='terms',
            resolver=get_dataset_glossary_terms,
            type=gql.Ref('TermSearchResult'),
        ),
        gql.Field(name='topics', type=gql.ArrayType(gql.Ref('Topic'))),
        gql.Field(name='confidentiality', type=gql.String),
        gql.Field(name='language', type=gql.Ref('Language')),
        gql.Field(
            name='projectPermission',
            args=[gql.Argument(name='projectUri', type=gql.NonNullableType(gql.String))],
            type=gql.Ref('DatasetRole'),
        ),
        gql.Field(
            name='isPublishedInEnvironment',
            args=[gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String))],
            type=gql.Boolean,
        ),
        gql.Field(name='stack', type=gql.Ref('Stack'), resolver=get_dataset_stack), ##todo: DECIDE
        gql.Field(name='autoApprovalEnabled', type=gql.Boolean),
    ],
)

DatasetSearchResult = gql.ObjectType(
    name='DatasetSearchResult',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='nodes', type=gql.ArrayType(Dataset)),
        gql.Field(name='pageSize', type=gql.Integer),
        gql.Field(name='nextPage', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='previousPage', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
    ],
)
