from ... import gql
from .input_types import OrganizationFilter
from .resolvers import *
from .schema import (
    Organization,
    OrganizationSearchResult,
)

getOrganization = gql.QueryField(
    name='getOrganization',
    args=[gql.Argument(name='organizationUri', type=gql.NonNullableType(gql.String))],
    type=gql.Thunk(lambda: Organization),
    resolver=get_organization,
    test_scope='Organization',
)


listOrganizations = gql.QueryField(
    name='listOrganizations',
    args=[gql.Argument('filter', OrganizationFilter)],
    type=OrganizationSearchResult,
    resolver=list_organizations,
    test_scope='Organization',
)

listOrganizationInvitedGroups = gql.QueryField(
    name='listOrganizationInvitedGroups',
    type=gql.Ref('GroupSearchResult'),
    args=[
        gql.Argument(name='organizationUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='filter', type=gql.Ref('GroupFilter')),
    ],
    resolver=list_organization_invited_groups,
)

listOrganizationGroups = gql.QueryField(
    name='listOrganizationGroups',
    type=gql.Ref('GroupSearchResult'),
    args=[
        gql.Argument(name='organizationUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='filter', type=gql.Ref('GroupFilter')),
    ],
    resolver=list_organization_groups,
)
