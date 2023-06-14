from ... import gql
from .resolvers import *

startDatasetProfilingRun = gql.MutationField(
    name='startDatasetProfilingRun',
    args=[gql.Argument(name='input', type=gql.Ref('StartDatasetProfilingRunInput'))],
    type=gql.Ref('DatasetProfilingRun'),
    resolver=start_profiling_run,
)
