from ... import gql
from .resolvers import get_group, list_datasets_owned_by_env_group, list_data_items_shared_with_env_group, list_cognito_groups

getGroup = gql.QueryField(
    name='getGroup',
    args=[gql.Argument(name='groupUri', type=gql.NonNullableType(gql.String))],
    type=gql.Ref('Group'),
    resolver=get_group,
)


listDatasetsOwnedByEnvGroup = gql.QueryField(
    name='listDatasetsOwnedByEnvGroup',
    type=gql.Ref('DatasetSearchResult'),
    args=[
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='groupUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='filter', type=gql.Ref('DatasetFilter')),
    ],
    resolver=list_datasets_owned_by_env_group,
    test_scope='Dataset',
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

listCognitoGroups = gql.QueryField(
    name='listCognitoGroups',
    args=[
        gql.Argument(name='filter', type=gql.Ref('CognitoGroupFilter')),
    ],
    type=gql.ArrayType(gql.Ref('CognitoGroup')),
    resolver=list_cognito_groups
)
