from dataall.base.api import gql
from dataall.modules.redshift_datasets.api.connections.resolvers import list_environment_redshift_connections

listEnvironmentRedshiftConnections = gql.QueryField(
    name='listEnvironmentRedshiftConnections',
    args=[gql.Argument('filter', gql.Ref('ConnectionFilter'))],
    type=gql.Ref('RedshiftConnectionSearchResult'),
    resolver=list_environment_redshift_connections,
)
