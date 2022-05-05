from ... import gql
from .resolvers import *
from ....api.constants import SagemakerStudioRole

SagemakerStudio = gql.ObjectType(
    name="SagemakerStudio",
    fields=[
        gql.Field(name="sagemakerStudioUri", type=gql.ID),
        gql.Field(name="environmentUri", type=gql.NonNullableType(gql.String)),
        gql.Field(name="label", type=gql.String),
        gql.Field(name="description", type=gql.String),
        gql.Field(name="tags", type=gql.ArrayType(gql.String)),
        gql.Field(name="name", type=gql.String),
        gql.Field(name="owner", type=gql.String),
        gql.Field(name="created", type=gql.String),
        gql.Field(name="updated", type=gql.String),
        gql.Field(name="SamlAdminGroupName", type=gql.String),
        gql.Field(
            name="userRoleForSagemakerStudio",
            type=SagemakerStudioRole.toGraphQLEnum(),
            resolver=resolve_user_role,
        ),
        gql.Field(name="SagemakerStudioStatus", type=gql.String, resolver=resolve_status),
        gql.Field(
            name="environment",
            type=gql.Ref("Environment"),
            resolver=resolve_environment,
        ),
        gql.Field(
            name="organization",
            type=gql.Ref("Organization"),
            resolver=resolve_organization,
        ),
        gql.Field(name="stack", type=gql.Ref("Stack"), resolver=resolve_stack),
    ],
)

SagemakerStudioSearchResult = gql.ObjectType(
    name="SagemakerStudioSearchResult",
    fields=[
        gql.Field(name="count", type=gql.Integer),
        gql.Field(name="page", type=gql.Integer),
        gql.Field(name="pages", type=gql.Integer),
        gql.Field(name="hasNext", type=gql.Boolean),
        gql.Field(name="hasPrevious", type=gql.Boolean),
        gql.Field(name="nodes", type=gql.ArrayType(SagemakerStudio)),
    ],
)

SagemakerStudioUserProfileApps = gql.ArrayType(
    gql.ObjectType(
        name="SagemakerStudioUserProfileApps",
        fields=[
            gql.Field(name="DomainId", type=gql.String),
            gql.Field(name="UserProfileName", type=gql.String),
            gql.Field(name="AppType", type=gql.String),
            gql.Field(name="AppName", type=gql.String),
            gql.Field(name="Status", type=gql.String),
        ],
    )
)

SagemakerStudioUserProfile = gql.ObjectType(
    name="SagemakerStudioUserProfile",
    fields=[
        gql.Field(name="sagemakerStudioUserProfileUri", type=gql.ID),
        gql.Field(name="environmentUri", type=gql.NonNullableType(gql.String)),
        gql.Field(name="label", type=gql.String),
        gql.Field(name="description", type=gql.String),
        gql.Field(name="tags", type=gql.ArrayType(gql.String)),
        gql.Field(name="name", type=gql.String),
        gql.Field(name="owner", type=gql.String),
        gql.Field(name="created", type=gql.String),
        gql.Field(name="updated", type=gql.String),
        gql.Field(name="SamlAdminGroupName", type=gql.String),
        gql.Field(
            name="userRoleForSagemakerStudioUserProfile",
            type=SagemakerStudioRole.toGraphQLEnum(),
            resolver=resolve_user_role,
        ),
        gql.Field(
            name="sagemakerStudioUserProfileStatus",
            type=gql.String,
            resolver=resolve_status,
        ),
        gql.Field(
            name="sagemakerStudioUserProfileApps",
            type=SagemakerStudioUserProfileApps,
            resolver=get_user_profile_applications,
        ),
        gql.Field(
            name="environment",
            type=gql.Ref("Environment"),
            resolver=resolve_environment,
        ),
        gql.Field(
            name="organization",
            type=gql.Ref("Organization"),
            resolver=resolve_organization,
        ),
        gql.Field(name="stack", type=gql.Ref("Stack"), resolver=resolve_stack),
    ],
)

SagemakerStudioUserProfileSearchResult = gql.ObjectType(
    name="SagemakerStudioUserProfileSearchResult",
    fields=[
        gql.Field(name="count", type=gql.Integer),
        gql.Field(name="page", type=gql.Integer),
        gql.Field(name="pages", type=gql.Integer),
        gql.Field(name="hasNext", type=gql.Boolean),
        gql.Field(name="hasPrevious", type=gql.Boolean),
        gql.Field(name="nodes", type=gql.ArrayType(SagemakerStudioUserProfile)),
    ],
)
