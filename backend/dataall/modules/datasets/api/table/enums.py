from dataall.base.api.constants import GraphQLEnumMapper


class DatasetTablePreviewStatus(GraphQLEnumMapper):
    QUEUED = 'QUEUED'
    RUNNING = 'RUNNING'
    SUCCEEDED = 'SUCCEEDED'
    FAILED = 'FAILED'
    CANCELLED = 'CANCELLED'
