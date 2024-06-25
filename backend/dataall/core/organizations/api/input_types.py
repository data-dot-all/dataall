from dataall.base.api.constants import GraphQLEnumMapper, SortDirection
from dataall.base.api import gql
from dataall.core.organizations.services.organizations_enums import OrganisationUserRole

NewOrganizationInput = gql.InputType(
    name='NewOrganizationInput',
    arguments=[
        gql.Argument(name='label', type=gql.String),
        gql.Argument(name='description', type=gql.String),
        gql.Argument(name='tags', type=gql.ArrayType(gql.String)),
        gql.Argument(name='SamlGroupName', type=gql.String),
    ],
)

ModifyOrganizationInput = gql.InputType(
    name='ModifyOrganizationInput',
    arguments=[
        gql.Argument('label', gql.String),
        gql.Argument(name='description', type=gql.String),
        gql.Argument(name='SamlGroupName', type=gql.String),
        gql.Argument(name='tags', type=gql.ArrayType(gql.String)),
    ],
)


class OrganizationSortField(GraphQLEnumMapper):
    created = 'created'
    updated = 'updated'
    label = 'label'


OrganizationSortCriteria = gql.InputType(
    name='OrganizationSortCriteria',
    arguments=[
        gql.Argument(
            name='field',
            type=gql.NonNullableType(OrganizationSortField.toGraphQLEnum()),
        ),
        gql.Argument(name='direction', type=gql.NonNullableType(SortDirection.toGraphQLEnum())),
    ],
)

OrganizationFilter = gql.InputType(
    name='OrganizationFilter',
    arguments=[
        gql.Argument('term', gql.String),
        gql.Argument('displayArchived', gql.Boolean),
        gql.Argument('sort', gql.ArrayType(OrganizationSortCriteria)),
        gql.Argument('page', gql.Integer),
        gql.Argument('pageSize', gql.Integer),
        gql.Argument('roles', gql.ArrayType(OrganisationUserRole.toGraphQLEnum())),
        gql.Argument('tags', gql.ArrayType(gql.String)),
    ],
)

InviteGroupToOrganizationInput = gql.InputType(
    name='InviteGroupToOrganizationInput',
    arguments=[
        gql.Argument('organizationUri', gql.NonNullableType(gql.String)),
        gql.Argument('groupUri', gql.NonNullableType(gql.String)),
        gql.Argument('permissions', gql.ArrayType(gql.String)),
    ],
)
