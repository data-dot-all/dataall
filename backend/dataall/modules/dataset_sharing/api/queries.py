from dataall.base.api import gql
from dataall.modules.dataset_sharing.api.resolvers import *

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

listDataItemsSharedWithEnvGroup = gql.QueryField(
    name='listDataItemsSharedWithEnvGroup',
    args=[
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='groupUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='filter', type=gql.Ref('EnvironmentDataItemFilter')),
    ],
    resolver=list_data_items_shared_with_env_group,
    type=gql.Ref('EnvironmentPublishedItemSearchResults'),
    test_scope='Dataset',
)

searchEnvironmentDataItems = gql.QueryField(
    name='searchEnvironmentDataItems',
    args=[
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='filter', type=gql.Ref('EnvironmentDataItemFilter')),
    ],
    resolver=list_shared_with_environment_data_items,
    type=gql.Ref('EnvironmentPublishedItemSearchResults'),
    test_scope='Dataset',
)
