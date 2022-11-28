from ... import gql
from .resolvers import *


getDatasetProfilingRun = gql.QueryField(
    name='getDatasetProfilingRun',
    args=[gql.Argument(name='profilingRunUri', type=gql.NonNullableType(gql.String))],
    type=gql.Ref('DatasetProfilingRun'),
    resolver=get_profiling_run,
)


listDatasetProfilingRuns = gql.QueryField(
    name='listDatasetProfilingRuns',
    args=[
        gql.Argument(name='datasetUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='filter', type=gql.Ref('DatasetProfilingRunFilter')),
    ],
    type=gql.Ref('DatasetProfilingRunSearchResults'),
    resolver=list_profiling_runs,
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
    resolver=get_last_table_profiling_run,
)
