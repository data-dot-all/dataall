from backend.api import gql
from backend.api.context import GraphQLEnumMapper
from .resolvers import *

class SagemakerNotebookRole(GraphQLEnumMapper):
    Creator = '950'
    Admin = '900'
    Shared = '300'
    NoPermission = '000'


EnvironmentSearchResult = gql.ObjectType(
    name='EnvironmentSearchResult',
    fields=[
        gql.Field(name='environmentUri', type=gql.ID),
        gql.Field(name='label', type=gql.String),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='description', type=gql.String),
        gql.Field(name='AwsAccountId', type=gql.String),
        gql.Field(name='region', type=gql.String)
    ],
)

OrganizationSearchResult = gql.ObjectType(
    name='OrganizationSearchResult',
    fields=[
        gql.Field(name='organizationUri', type=gql.ID),
        gql.Field(name='label', type=gql.String),
        gql.Field(name='name', type=gql.String)
    ],
)

SagemakerNotebook = gql.ObjectType(
    name='SagemakerNotebook',
    fields=[
        gql.Field(name='notebookUri', type=gql.ID),
        gql.Field(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Field(name='label', type=gql.String),
        gql.Field(name='description', type=gql.String),
        gql.Field(name='tags', type=gql.ArrayType(gql.String)),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='owner', type=gql.String),
        gql.Field(name='created', type=gql.String),
        gql.Field(name='updated', type=gql.String),
        gql.Field(name='SamlAdminGroupName', type=gql.String),
        gql.Field(name='VpcId', type=gql.String),
        gql.Field(name='SubnetId', type=gql.String),
        gql.Field(name='InstanceType', type=gql.String),
        gql.Field(name='RoleArn', type=gql.String),
        gql.Field(name='VolumeSizeInGB', type=gql.Integer),
        gql.Field(
            name='userRoleForNotebook',
            type=SagemakerNotebookRole.toGraphQLEnum(),
            resolver=resolve_user_role,
        ),
        gql.Field(
            name='NotebookInstanceStatus', type=gql.String, resolver=resolve_status
        ),
        gql.Field(
            name='environment',
            type=gql.Ref('EnvironmentSearchResult'),
            resolver=resolve_environment,
        ),
        gql.Field(
            name='organization',
            type=gql.Ref('OrganizationSearchResult'),
            resolver=resolve_organization,
        ),
        gql.Field(name='stack', type=gql.Ref('StackSearchResult'), resolver=resolve_stack),
    ],
)

StackSearchResult = gql.ObjectType(
    name='StackSearchResult',
    fields=[
        gql.Field(name='stack', type=gql.NonNullableType(gql.String)),
        gql.Field(name='status', type=gql.String)
    ],
)
##TODO add the part of resolvers of Stack = Stack should be part of common
SagemakerNotebookSearchResult = gql.ObjectType(
    name='SagemakerNotebookSearchResult',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(SagemakerNotebook)),
    ],
)
