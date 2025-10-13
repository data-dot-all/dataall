from dataall.base.api import gql
from dataall.modules.datasets_base.services.datasets_enums import DatasetRole
from dataall.modules.datasets_base.api.resolvers import (
    get_dataset_environment,
    get_dataset_organization,
    get_dataset_owners_group,
    get_dataset_stewards_group,
    resolve_user_role,
    resolve_dataset_stack,
)
from dataall.core.environment.api.enums import EnvironmentPermission

DatasetBase = gql.ObjectType(
    name='DatasetBase',
    fields=[
        gql.Field(name='datasetUri', type=gql.ID),
        gql.Field(name='datasetType', type=gql.String),
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
        gql.Field(name='imported', type=gql.Boolean),
        gql.Field(
            name='environment',
            type=gql.Ref('EnvironmentSimplified'),
            resolver=get_dataset_environment,
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
        gql.Field(
            name='userRoleForDataset',
            type=DatasetRole.toGraphQLEnum(),
            resolver=resolve_user_role,
        ),
        gql.Field(name='userRoleInEnvironment', type=EnvironmentPermission.toGraphQLEnum()),
        gql.Field(name='topics', type=gql.ArrayType(gql.Ref('Topic'))),
        gql.Field(name='confidentiality', type=gql.String),
        gql.Field(name='language', type=gql.Ref('Language')),
        gql.Field(name='autoApprovalEnabled', type=gql.Boolean),
        gql.Field(name='stack', type=gql.Ref('Stack'), resolver=resolve_dataset_stack),
    ],
)

DatasetBaseSearchResult = gql.ObjectType(
    name='DatasetBaseSearchResult',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='nodes', type=gql.ArrayType(DatasetBase)),
        gql.Field(name='pageSize', type=gql.Integer),
        gql.Field(name='nextPage', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='previousPage', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
    ],
)
