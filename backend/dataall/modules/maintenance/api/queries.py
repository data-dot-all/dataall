"""The module defines GraphQL queries for the SageMaker notebooks"""

from dataall.base.api import gql
from dataall.modules.maintenance.api.resolvers import get_maintenance_window_status, get_maintenance_window_mode


getMaintenanceWindowStatus = gql.QueryField(
    name='getMaintenanceWindowStatus',
    type=gql.Ref('Maintenance'),
    resolver=get_maintenance_window_status
)

getMaintenanceWindowMode = gql.QueryField(
    name='getMaintenanceWindowMode',
    type=gql.String,
    resolver=get_maintenance_window_mode
)
