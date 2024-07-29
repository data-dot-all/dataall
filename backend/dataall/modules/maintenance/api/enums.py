"""Contains the enums used in maintenance module"""

from dataall.base.api import GraphQLEnumMapper


class MaintenanceModes(GraphQLEnumMapper):
    """Describes the Maintenance Modes"""

    READONLY = 'READ-ONLY'
    NOACCESS = 'NO-ACCESS'


class MaintenanceStatus(GraphQLEnumMapper):
    """Describe the various statuses for maintenance"""

    PENDING = 'PENDING'
    INACTIVE = 'INACTIVE'
    ACTIVE = 'ACTIVE'
