from dataall.base.api import gql
from .input_types import OrganizationFilter
from .resolvers import (
    get_organization,
    list_organization_groups,
    list_organizations,
    list_group_organization_permissions,
    list_invited_organization_permissions_with_descriptions,
)
from .types import (
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

listOrganizationGroups = gql.QueryField(
    name='listOrganizationGroups',
    type=gql.Ref('GroupSearchResult'),
    args=[
        gql.Argument(name='organizationUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='filter', type=gql.Ref('GroupFilter')),
    ],
    resolver=list_organization_groups,
)

listOrganizationGroupPermissions = gql.QueryField(
    name='listOrganizationGroupPermissions',
    type=gql.ArrayType(gql.Ref('Permission')),
    args=[
        gql.Argument(name='organizationUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='groupUri', type=gql.NonNullableType(gql.String)),
    ],
    resolver=list_group_organization_permissions,
)

listInviteOrganizationPermissionsWithDescriptions = gql.QueryField(
    name='listInviteOrganizationPermissionsWithDescriptions',
    type=gql.ArrayType(gql.Ref('DescribedPermission')),
    resolver=list_invited_organization_permissions_with_descriptions,
)
