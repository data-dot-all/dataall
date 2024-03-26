from dataall.base.api import gql
from dataall.modules.datasets_base.api.input_types import DatasetFilter
from dataall.modules.datasets_base.api.resolvers import (
    list_owned_datasets,
    #list_dataset_share_objects,
    list_datasets_owned_by_env_group,
    list_datasets_created_in_environment,
)
from dataall.modules.datasets_base.api.types import DatasetSearchResult

# TODO: do something about the dependency with shared databases
# listDatasets = gql.QueryField(
#     name='listDatasets',
#     args=[gql.Argument('filter', DatasetFilter)],
#     type=DatasetSearchResult,
#     resolver=list_owned_shared_datasets,
#     test_scope='Dataset',
# )

listOwnedDatasets = gql.QueryField(
    name='listOwnedDatasets',
    args=[gql.Argument('filter', DatasetFilter)],
    type=DatasetSearchResult,
    resolver=list_owned_datasets,
    test_scope='Dataset',
)


# listShareObjects = gql.QueryField(
#     name='listDatasetShareObjects',
#     resolver=list_dataset_share_objects,
#     args=[
#         gql.Argument(name='datasetUri', type=gql.NonNullableType(gql.String)),
#         gql.Argument(name='environmentUri', type=gql.String),
#         gql.Argument(name='page', type=gql.Integer),
#     ],
#     type=gql.Ref('ShareSearchResult'),
# )

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

listDatasetsCreatedInEnvironment = gql.QueryField(
    name='listDatasetsCreatedInEnvironment',
    type=gql.Ref('DatasetSearchResult'),
    args=[
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='filter', type=gql.Ref('DatasetFilter')),
    ],
    resolver=list_datasets_created_in_environment,
    test_scope='Dataset',
)
