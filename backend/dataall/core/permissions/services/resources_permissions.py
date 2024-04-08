from dataall.core.permissions.services.organization_permissions import ORGANIZATION_ALL
from dataall.core.permissions.services.environment_permissions import (
    CREATE_NETWORK,
    ENVIRONMENT_ALL,
    CONSUMPTION_ROLE_ALL,
    INVITE_ENVIRONMENT_GROUP,
    ADD_ENVIRONMENT_CONSUMPTION_ROLES,
)
from dataall.core.permissions.services.network_permissions import NETWORK_ALL

"""
RESOURCES_ALL
"""
RESOURCES_ALL = ORGANIZATION_ALL + ENVIRONMENT_ALL + CONSUMPTION_ROLE_ALL + NETWORK_ALL

RESOURCES_ALL_WITH_DESC = {k: k for k in RESOURCES_ALL}
RESOURCES_ALL_WITH_DESC[INVITE_ENVIRONMENT_GROUP] = 'Invite other teams to this environment'
RESOURCES_ALL_WITH_DESC[ADD_ENVIRONMENT_CONSUMPTION_ROLES] = 'Add IAM consumption roles to this environment'
RESOURCES_ALL_WITH_DESC[CREATE_NETWORK] = 'Create networks on this environment'
