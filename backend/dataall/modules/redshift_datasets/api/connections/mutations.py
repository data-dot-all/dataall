from dataall.base.api import gql
from dataall.modules.redshift_datasets.api.connections.resolvers import (
    create_redshift_connection,
    delete_redshift_connection,
)
from dataall.modules.redshift_datasets.api.connections.types import (
    RedshiftConnection,
)

createRedshiftConnection = gql.MutationField(
    name='createRedshiftConnection',
    args=[gql.Argument(name='input', type=gql.Ref('CreateRedshiftConnectionInput'))],
    type=RedshiftConnection,
    resolver=create_redshift_connection,
)

deleteRedshiftConnection = gql.MutationField(
    name='deleteRedshiftConnection',
    args=[gql.Argument(name='connectionUri', type=gql.NonNullableType(gql.String))],
    type=gql.Boolean,
    resolver=delete_redshift_connection,
)
