from ... import gql
from .resolvers import *

listTenantPermissions = gql.QueryField(
    name='listTenantPermissions',
    args=[
        gql.Argument(name='filter', type=gql.Ref('TenantPermissionFilter')),
    ],
    type=gql.Ref('PermissionSearchResult'),
    resolver=list_tenant_permissions,
)

listResourcePermissions = gql.QueryField(
    name='listResourcePermissions',
    args=[
        gql.Argument(name='filter', type=gql.Ref('ResourcePermissionFilter')),
    ],
    type=gql.Ref('PermissionSearchResult'),
    resolver=list_resource_permissions,
)
