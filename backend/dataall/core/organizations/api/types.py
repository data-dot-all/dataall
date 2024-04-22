from dataall.base.api import gql
from dataall.core.organizations.api.resolvers import resolve_user_role, list_organization_environments, stats
from dataall.core.organizations.services.organizations_enums import OrganisationUserRole

OrganizationStats = gql.ObjectType(
    name='OrganizationStats',
    fields=[
        gql.Field(name='groups', type=gql.Integer),
        gql.Field(name='users', type=gql.Integer),
        gql.Field(name='environments', type=gql.Integer),
    ],
)
Organization = gql.ObjectType(
    name='Organization',
    fields=[
        gql.Field(name='organizationUri', type=gql.ID),
        gql.Field(name='label', type=gql.String),
        gql.Field(name='name', type=gql.String),
        gql.Field(name='description', type=gql.String),
        gql.Field(name='tags', type=gql.ArrayType(gql.String)),
        gql.Field(name='owner', type=gql.String),
        gql.Field(name='SamlGroupName', type=gql.String),
        gql.Field(
            name='userRoleInOrganization',
            type=OrganisationUserRole.toGraphQLEnum(),
            resolver=resolve_user_role,
        ),
        gql.Field(
            name='environments',
            args=[gql.Argument(name='filter', type=gql.Ref('EnvironmentFilter'))],
            type=gql.Ref('EnvironmentSearchResult'),
            resolver=list_organization_environments,
        ),
        gql.Field(name='created', type=gql.String),
        gql.Field(name='updated', type=gql.String),
        gql.Field(name='stats', type=OrganizationStats, resolver=stats),
    ],
)

OrganizationSearchResult = gql.ObjectType(
    name='OrganizationSearchResult',
    fields=[
        gql.Field(name='count', type=gql.Integer),
        gql.Field(name='pageSize', type=gql.Integer),
        gql.Field(name='nextPage', type=gql.Integer),
        gql.Field(name='pages', type=gql.Integer),
        gql.Field(name='page', type=gql.Integer),
        gql.Field(name='previousPage', type=gql.Integer),
        gql.Field(name='hasNext', type=gql.Boolean),
        gql.Field(name='hasPrevious', type=gql.Boolean),
        gql.Field(name='nodes', type=gql.ArrayType(Organization)),
    ],
)

OrganizationSimplified = gql.ObjectType(
    name='OrganizationSimplified',
    fields=[
        gql.Field(name='organizationUri', type=gql.ID),
        gql.Field(name='label', type=gql.String),
        gql.Field(name='name', type=gql.String),
    ],
)
