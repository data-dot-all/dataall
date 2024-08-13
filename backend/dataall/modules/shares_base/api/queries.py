from dataall.base.api import gql
from dataall.modules.shares_base.api.resolvers import (
    get_share_object,
    get_share_logs,
    list_shared_with_environment_data_items,
    list_shares_in_my_inbox,
    list_shares_in_my_outbox,
    get_share_item_data_filters,
)

getShareObject = gql.QueryField(
    name='getShareObject',
    args=[gql.Argument(name='shareUri', type=gql.NonNullableType(gql.String))],
    type=gql.Ref('ShareObject'),
    resolver=get_share_object,
)

getShareRequestsFromMe = gql.QueryField(
    name='getShareRequestsFromMe',
    args=[gql.Argument(name='filter', type=gql.Ref('ShareObjectFilter'))],
    type=gql.Ref('ShareSearchResult'),
    resolver=list_shares_in_my_outbox,
)

getShareRequestsToMe = gql.QueryField(
    name='getShareRequestsToMe',
    args=[gql.Argument(name='filter', type=gql.Ref('ShareObjectFilter'))],
    type=gql.Ref('ShareSearchResult'),
    resolver=list_shares_in_my_inbox,
)

searchEnvironmentDataItems = gql.QueryField(
    name='searchEnvironmentDataItems',
    args=[
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='filter', type=gql.Ref('EnvironmentDataItemFilter')),
    ],
    resolver=list_shared_with_environment_data_items,
    type=gql.Ref('EnvironmentPublishedItemSearchResults'),
)

getShareLogs = gql.QueryField(
    name='getShareLogs',
    args=[gql.Argument(name='shareUri', type=gql.NonNullableType(gql.String))],
    type=gql.ArrayType(gql.Ref('ShareLog')),
    resolver=get_share_logs,
)

getShareItemDataFilters = gql.QueryField(
    name='getShareItemDataFilters',
    args=[
        gql.Argument(name='attachedDataFilterUri', type=gql.NonNullableType(gql.String)),
    ],
    type=gql.Ref('ShareObjectItemDataFilter'),
    resolver=get_share_item_data_filters,
)
