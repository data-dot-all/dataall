from ... import gql
from .resolvers import *


listTenantLFTags = gql.QueryField(
    name='listTenantLFTags',
    args=[
        gql.Argument(name='filter', type=gql.Ref('LFTagFilter')),
    ],
    type=gql.Ref('LFTagSearchResult'),
    resolver=list_tenant_lf_tags,
)
