from ... import gql
from .resolvers import *


listTenantLFTagPermissions = gql.QueryField(
    name='listTenantLFTagPermissions',
    args=[
        gql.Argument(name='filter', type=gql.Ref('LFTagPermissionsFilter')),
    ],
    type=gql.Ref('LFTagPermissionSearchResult'),
    resolver=list_tenant_lf_tag_permissions,
)
