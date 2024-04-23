"""Contains the enums GraphQL mapping for SageMaker notebooks"""

from dataall.base.api.constants import GraphQLEnumMapper


class MaintenanceModes(GraphQLEnumMapper):
    """Describes the Maintenance Modes"""

    READONLY = 'READ-ONLY'
    NOACCESS = 'NO-ACCESS'

class MaintenanceStatus():
    """Describe the various statuses for maintenance"""

    PENDING = 'PENDING'
    INACTIVE = 'INACTIVE'
    ACTIVE = 'ACTIVE'
