from dataall.base.api import gql
from dataall.modules.redshift_datasets.api.connections.resolvers import (
    add_redshift_connection_group_permissions,
    create_redshift_connection,
    delete_redshift_connection,
    delete_redshift_connection_group_permissions,
)
from dataall.modules.redshift_datasets.api.connections.types import (
    RedshiftConnection,
)

createRedshiftConnection = gql.MutationField(
    name='createRedshiftConnection',
    args=[gql.Argument('input', gql.Ref('CreateRedshiftConnectionInput'))],
    type=RedshiftConnection,
    resolver=create_redshift_connection,
)

deleteRedshiftConnection = gql.MutationField(
    name='deleteRedshiftConnection',
    args=[gql.Argument('connectionUri', gql.NonNullableType(gql.String))],
    type=gql.Boolean,
    resolver=delete_redshift_connection,
)

addConnectionGroupPermission = gql.MutationField(
    name='addConnectionGroupPermission',
    args=[
        gql.Argument('connectionUri', gql.NonNullableType(gql.String)),
        gql.Argument('groupUri', gql.NonNullableType(gql.String)),
        gql.Argument('permissions', gql.NonNullableType(gql.ArrayType(gql.String))),
    ],
    type=gql.Boolean,
    resolver=add_redshift_connection_group_permissions,
)

deleteConnectionGroupPermission = gql.MutationField(
    name='deleteConnectionGroupPermission',
    args=[
        gql.Argument('connectionUri', gql.NonNullableType(gql.String)),
        gql.Argument('groupUri', gql.NonNullableType(gql.String)),
    ],
    type=gql.Boolean,
    resolver=delete_redshift_connection_group_permissions,
)
