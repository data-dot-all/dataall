from dataall.api import gql
from .resolvers import *


listTenantPermissions = gql.QueryField(
    name='listTenantPermissions',
    args=[
        gql.Argument(name='filter', type=gql.Ref('TenantPermissionFilter')),
    ],
    type=gql.Ref('PermissionSearchResult'),
    resolver=list_tenant_permissions,
)
