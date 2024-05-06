from dataall.base.api import gql
from dataall.modules.s3_datasets.api.profiling.resolvers import (
    list_table_profiling_runs,
    get_dataset_table_profiling_run,
)

listDatasetTableProfilingRuns = gql.QueryField(
    name='listDatasetTableProfilingRuns',
    args=[gql.Argument(name='tableUri', type=gql.NonNullableType(gql.String))],
    type=gql.Ref('DatasetProfilingRunSearchResults'),
    resolver=list_table_profiling_runs,
)

getDatasetTableLastProfilingRun = gql.QueryField(
    name='getDatasetTableProfilingRun',
    args=[gql.Argument(name='tableUri', type=gql.NonNullableType(gql.String))],
    type=gql.Ref('DatasetProfilingRun'),
    resolver=get_dataset_table_profiling_run,
)
