"""The module defines GraphQL input types for the Maintenance Window Activity"""

from dataall.base.api import gql

MaintenanceWindowInput = gql.InputType(
    name='MaintenanceWindowInput',
    arguments=[
        gql.Argument('status', gql.NonNullableType(gql.String)),
        gql.Argument('mode', gql.String),
    ],
)