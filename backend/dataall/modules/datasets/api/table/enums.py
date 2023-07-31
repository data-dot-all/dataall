from dataall.base.api.constants import GraphQLEnumMapper


class DatasetSortField(GraphQLEnumMapper):
    created = 'created'
    updated = 'updated'
    label = 'label'


class DatasetTablePreviewStatus(GraphQLEnumMapper):
    QUEUED = 'QUEUED'
    RUNNING = 'RUNNING'
    SUCCEEDED = 'SUCCEEDED'
    FAILED = 'FAILED'
    CANCELLED = 'CANCELLED'
