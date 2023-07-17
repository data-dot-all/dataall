from .resolvers import *
from ...constants import *


Group = gql.ObjectType(
    name='Group',
    fields=[
        gql.Field(name='groupUri', type=gql.String),
        gql.Field(name='invitedBy', type=gql.String),
        gql.Field(name='owner', type=gql.String),
        gql.Field(name='label', type=gql.String),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='description', type=gql.String),
        gql.Field(name='tags', type=gql.ArrayType(gql.String)),
        gql.Field(name='created', type=gql.String),
        gql.Field(name='updated', type=gql.String),
        gql.Field(name='environmentIAMRoleArn', type=gql.String),
        gql.Field(name='environmentIAMRoleName', type=gql.String),
        gql.Field(name='environmentAthenaWorkGroup', type=gql.String),
        gql.Field(
            name='environmentPermissions',
            args=[
                gql.Argument(
                    name='environmentUri', type=gql.NonNullableType(gql.String)
                )
            ],
            type=gql.ArrayType(gql.Ref('Permission')),
            resolver=resolve_group_environment_permissions,
        ),
        gql.Field(
            name='tenantPermissions',
            type=gql.ArrayType(gql.Ref('Permission')),
            resolver=resolve_group_tenant_permissions,
        ),
    ],
)

GroupSearchResult = gql.ObjectType(
    name='GroupSearchResult',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(Group)),
    ],
)

CognitoGroup = gql.ObjectType(
    name='CognitoGroup',
    fields=[
        gql.Field(name='groupName', type=gql.String),
    ],
)
