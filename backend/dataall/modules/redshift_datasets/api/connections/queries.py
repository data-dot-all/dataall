from dataall.base.api import gql
from dataall.modules.redshift_datasets.api.connections.resolvers import (
    list_environment_redshift_connections,
    list_redshift_connection_group_no_permissions,
    list_redshift_connection_group_permissions,
    list_redshift_connection_schemas,
    list_redshift_schema_tables,
)

listEnvironmentRedshiftConnections = gql.QueryField(
    name='listEnvironmentRedshiftConnections',
    args=[gql.Argument('filter', gql.Ref('ConnectionFilter'))],
    type=gql.Ref('RedshiftConnectionSearchResult'),
    resolver=list_environment_redshift_connections,
)

listRedshiftConnectionSchemas = gql.QueryField(
    name='listRedshiftConnectionSchemas',
    args=[gql.Argument('connectionUri', gql.NonNullableType(gql.String))],
    type=gql.ArrayType(gql.String),
    resolver=list_redshift_connection_schemas,
)

listRedshiftSchemaTables = gql.QueryField(
    name='listRedshiftSchemaTables',
    args=[
        gql.Argument('connectionUri', gql.NonNullableType(gql.String)),
        gql.Argument('schema', gql.NonNullableType(gql.String)),
    ],
    type=gql.ArrayType(gql.Ref('RedshiftTable')),
    resolver=list_redshift_schema_tables,
)

listConnectionGroupPermissions = gql.QueryField(
    name='listConnectionGroupPermissions',
    type=gql.Ref('ConnectionGroupSearchResult'),
    args=[
        gql.Argument(name='connectionUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='filter', type=gql.Ref('GroupFilter')),
    ],
    resolver=list_redshift_connection_group_permissions,
)

listConnectionGroupNoPermissions = gql.QueryField(
    name='listConnectionGroupNoPermissions',
    type=gql.ArrayType(gql.String),
    args=[
        gql.Argument(name='connectionUri', type=gql.NonNullableType(gql.String)),
        gql.Argument(name='filter', type=gql.Ref('GroupFilter')),
    ],
    resolver=list_redshift_connection_group_no_permissions,
)
