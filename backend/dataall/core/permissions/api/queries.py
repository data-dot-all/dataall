from dataall.base.api import gql
from .resolvers import (
    list_tenant_groups,
    list_tenant_permissions,
    list_invited_organization_permissions_with_descriptions,
)

listTenantPermissions = gql.QueryField(
    name='listTenantPermissions',
    type=gql.ArrayType(gql.Ref('Permission')),
    resolver=list_tenant_permissions,
)

listTenantGroups = gql.QueryField(
    name='listTenantGroups',
    args=[
        gql.Argument(name='filter', type=gql.Ref('GroupFilter')),
    ],
    type=gql.Ref('GroupSearchResult'),
    resolver=list_tenant_groups,
)

listInviteOrganizationPermissionsWithDescriptions = gql.QueryField(
    name='listInviteOrganizationPermissionsWithDescriptions',
    type=gql.ArrayType(gql.Ref('DescribedPermission')),
    resolver=list_invited_organization_permissions_with_descriptions,
)
