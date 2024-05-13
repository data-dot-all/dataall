from dataall.base.api import gql
from dataall.modules.dataset_sharing.api.resolvers import (
    get_dataset_shared_assume_role_url,
    get_share_object,
    list_shared_with_environment_data_items,
    list_shares_in_my_inbox,
    list_shares_in_my_outbox,
    list_dataset_share_objects,
    list_shared_tables_by_env_dataset,
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
    test_scope='Dataset',
)

listShareObjects = gql.QueryField(
    name='listDatasetShareObjects',
    resolver=list_dataset_share_objects,
    args=[
        gql.Argument(name='datasetUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='environmentUri', type=gql.String),
        gql.Argument(name='page', type=gql.Integer),
    ],
    type=gql.Ref('ShareSearchResult'),
)

getSharedDatasetTables = gql.QueryField(
    name='getSharedDatasetTables',
    args=[
        gql.Argument(name='datasetUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='envUri', type=gql.NonNullableType(gql.String)),
    ],
    type=gql.ArrayType(gql.Ref('SharedDatasetTableItem')),
    resolver=list_shared_tables_by_env_dataset,
)

getDatasetSharedAssumeRoleUrl = gql.QueryField(
    name='getDatasetSharedAssumeRoleUrl',
    args=[gql.Argument(name='datasetUri', type=gql.String)],
    type=gql.String,
    resolver=get_dataset_shared_assume_role_url,
    test_scope='Dataset',
)
