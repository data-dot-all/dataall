"""The module defines GraphQL queries for the Maintenance Activity>"""

from dataall.base.api import gql
from dataall.modules.maintenance.api.resolvers import get_maintenance_window_status


getMaintenanceWindowStatus = gql.QueryField(
    name='getMaintenanceWindowStatus', type=gql.Ref('Maintenance'), resolver=get_maintenance_window_status
)
