from dataall.base.api import gql
from dataall.modules.datasets_base.api.input_types import DatasetFilter
from dataall.modules.datasets_base.api.resolvers import (
    list_all_user_datasets,
    list_datasets_created_in_environment,
    list_owned_datasets,
)
from dataall.modules.datasets_base.api.types import DatasetBaseSearchResult

listDatasets = gql.QueryField(
    name='listDatasets',
    args=[gql.Argument('filter', DatasetFilter)],
    type=DatasetBaseSearchResult,
    resolver=list_all_user_datasets,
)

listOwnedDatasets = gql.QueryField(
    name='listOwnedDatasets',
    args=[gql.Argument('filter', DatasetFilter)],
    type=DatasetBaseSearchResult,
    resolver=list_owned_datasets,
)

listDatasetsCreatedInEnvironment = gql.QueryField(
    name='listDatasetsCreatedInEnvironment',
    type=DatasetBaseSearchResult,
    args=[
        gql.Argument(name='environmentUri', type=gql.NonNullableType(gql.String)),
        gql.Argument('filter', DatasetFilter),
    ],
    resolver=list_datasets_created_in_environment,
)
