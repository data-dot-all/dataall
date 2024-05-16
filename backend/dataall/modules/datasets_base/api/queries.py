from dataall.base.api import gql
from dataall.modules.datasets_base.api.input_types import DatasetFilter
from dataall.modules.datasets_base.api.resolvers import (
    list_all_user_datasets,
)
from dataall.modules.datasets_base.api.types import DatasetBaseSearchResult

listDatasets = gql.QueryField(
    name='listDatasets',
    args=[gql.Argument('filter', DatasetFilter)],
    type=DatasetBaseSearchResult,
    resolver=list_all_user_datasets,
    test_scope='Dataset',
)
