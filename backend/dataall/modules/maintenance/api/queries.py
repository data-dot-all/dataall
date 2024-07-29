"""The module defines GraphQL queries for the Maintenance Activity>"""

from dataall.base.api import gql
from dataall.base.utils.enum_utils import generate_enum_query
from dataall.modules.maintenance.api.enums import MaintenanceModes, MaintenanceStatus
from dataall.modules.maintenance.api.resolvers import get_maintenance_window_status


getMaintenanceWindowStatus = gql.QueryField(
    name='getMaintenanceWindowStatus', type=gql.Ref('Maintenance'), resolver=get_maintenance_window_status
)

queryMaintenanceModes = generate_enum_query(MaintenanceModes, 'Maintenance')

queryMaintenanceStatus = generate_enum_query(MaintenanceStatus, 'Maintenance')
