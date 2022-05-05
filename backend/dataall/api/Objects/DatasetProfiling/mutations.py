from ... import gql
from .resolvers import *

startDatasetProfilingRun = gql.MutationField(
    name="startDatasetProfilingRun",
    args=[gql.Argument(name="input", type=gql.Ref("StartDatasetProfilingRunInput"))],
    type=gql.Ref("DatasetProfilingRun"),
    resolver=start_profiling_run,
)

updateDatasetProfilingRunResults = gql.MutationField(
    name="updateDatasetProfilingRunResults",
    args=[
        gql.Argument(name="profilingRunUri", type=gql.NonNullableType(gql.String)),
        gql.Argument(name="results", type=gql.NonNullableType(gql.String)),
    ],
    type=gql.Ref("DatasetProfilingRun"),
    resolver=update_profiling_run_results,
)
