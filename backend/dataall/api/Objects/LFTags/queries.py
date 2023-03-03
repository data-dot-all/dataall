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

listLFTagsAll = gql.QueryField(
    name='listLFTagsAll',
    type=gql.ArrayType(gql.Ref('LFTag')),
    # args=[
    #     gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String))
    # ],
    resolver=list_all_lf_tags,
)
