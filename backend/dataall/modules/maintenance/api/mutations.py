"""The module defines GraphQL mutations for the Maintenance Window Activity"""

from dataall.base.api import gql
from dataall.modules.maintenance.api.resolvers import start_maintenance_window, stop_maintenance_window


startMaintenanceWindow = gql.MutationField(
    name='startMaintenanceWindow',
    args=[gql.Argument(name='mode', type=gql.String)],
    type=gql.Boolean,
    resolver=start_maintenance_window,
)

stopMaintenanceWindow = gql.MutationField(
    name='stopMaintenanceWindow',
    type=gql.Boolean,
    resolver=stop_maintenance_window,
)
