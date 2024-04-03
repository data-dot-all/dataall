"""Defines the object types of the SageMaker ML Studio"""

from dataall.base.api import gql
from dataall.modules.mlstudio.api.resolvers import (
    resolve_user_role,
    resolve_sagemaker_studio_user_status,
    resolve_sagemaker_studio_user_stack,
    resolve_sagemaker_studio_user_applications,
)
from dataall.modules.mlstudio.api.enums import SagemakerStudioRole


from dataall.core.organizations.api.resolvers import resolve_organization_by_env
from dataall.core.environment.api.resolvers import resolve_environment


SagemakerStudioUserApps = gql.ArrayType(
    gql.ObjectType(
        name='SagemakerStudioUserApps',
        fields=[
            gql.Field(name='DomainId', type=gql.String),
            gql.Field(name='UserName', type=gql.String),
            gql.Field(name='AppType', type=gql.String),
            gql.Field(name='AppName', type=gql.String),
            gql.Field(name='Status', type=gql.String),
        ],
    )
)

SagemakerStudioUser = gql.ObjectType(
    name='SagemakerStudioUser',
    fields=[
        gql.Field(name='sagemakerStudioUserUri', type=gql.ID),
        gql.Field(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Field(name='label', type=gql.String),
        gql.Field(name='description', type=gql.String),
        gql.Field(name='tags', type=gql.ArrayType(gql.String)),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='owner', type=gql.String),
        gql.Field(name='created', type=gql.String),
        gql.Field(name='updated', type=gql.String),
        gql.Field(name='SamlAdminGroupName', type=gql.String),
        gql.Field(
            name='userRoleForSagemakerStudioUser',
            type=SagemakerStudioRole.toGraphQLEnum(),
            resolver=resolve_user_role,
        ),
        gql.Field(
            name='sagemakerStudioUserStatus',
            type=gql.String,
            resolver=resolve_sagemaker_studio_user_status,
        ),
        gql.Field(
            name='sagemakerStudioUserApps',
            type=SagemakerStudioUserApps,
            resolver=resolve_sagemaker_studio_user_applications,
        ),
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
        gql.Field(name='stack', type=gql.Ref('Stack'), resolver=resolve_sagemaker_studio_user_stack),
    ],
)

SagemakerStudioUserSearchResult = gql.ObjectType(
    name='SagemakerStudioUserSearchResult',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(SagemakerStudioUser)),
    ],
)

SagemakerStudioDomain = gql.ObjectType(
    name='SagemakerStudioDomain',
    fields=[
        gql.Field(name='sagemakerStudioUri', type=gql.ID),
        gql.Field(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Field(name='sagemakerStudioDomainName', type=gql.String),
        gql.Field(name='DefaultDomainRoleName', type=gql.String),
        gql.Field(name='label', type=gql.String),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='vpcType', type=gql.String),
        gql.Field(name='vpcId', type=gql.String),
        gql.Field(name='subnetIds', type=gql.ArrayType(gql.String)),
        gql.Field(name='owner', type=gql.String),
        gql.Field(name='created', type=gql.String),
        gql.Field(name='updated', type=gql.String),
        gql.Field(name='deleted', type=gql.String),
        gql.Field(
            name='environment',
            type=gql.Ref('Environment'),
            resolver=resolve_environment,
        ),
    ],
)
