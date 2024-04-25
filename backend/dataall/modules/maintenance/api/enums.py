"""Contains the enums used in maintenance module"""

from enum import Enum


class MaintenanceModes(Enum):
    """Describes the Maintenance Modes"""

    READONLY = 'READ-ONLY'
    NOACCESS = 'NO-ACCESS'


class MaintenanceStatus(Enum):
    """Describe the various statuses for maintenance"""

    PENDING = 'PENDING'
    INACTIVE = 'INACTIVE'
    ACTIVE = 'ACTIVE'
