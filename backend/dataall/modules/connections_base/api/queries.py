from dataall.base.api import gql
from dataall.modules.connections_base.api.resolvers import (
    list_environment_connections
)
listEnvironmentConnections = gql.QueryField(
    name='listEnvironmentConnections',
    args=[gql.Argument('filter', gql.Ref('ConnectionFilter'))],
    type=gql.Ref('ConnectionSearchResult'),
    resolver=list_environment_connections,
)

