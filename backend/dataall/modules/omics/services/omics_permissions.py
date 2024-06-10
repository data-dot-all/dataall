"""
Add module's permissions to the global permissions.
Contains permissions for Omics RUNs
"""

from dataall.core.permissions.services.environment_permissions import (
    ENVIRONMENT_INVITED,
    ENVIRONMENT_INVITATION_REQUEST,
    ENVIRONMENT_ALL,
)
from dataall.core.permissions.services.resources_permissions import (
    RESOURCES_ALL_WITH_DESC,
    RESOURCES_ALL,
)
from dataall.core.permissions.services.tenant_permissions import TENANT_ALL, TENANT_ALL_WITH_DESC

DELETE_OMICS_RUN = 'DELETE_OMICS_RUN'
CREATE_OMICS_RUN = 'CREATE_OMICS_RUN'
MANAGE_OMICS_RUNS = 'MANAGE_OMICS_RUNS'

OMICS_RUN_ALL = [
    DELETE_OMICS_RUN,
]

ENVIRONMENT_ALL.append(CREATE_OMICS_RUN)
ENVIRONMENT_INVITED.append(CREATE_OMICS_RUN)
ENVIRONMENT_INVITATION_REQUEST.append(CREATE_OMICS_RUN)

TENANT_ALL.append(MANAGE_OMICS_RUNS)
TENANT_ALL_WITH_DESC[MANAGE_OMICS_RUNS] = 'Manage Omics workflow runs'


RESOURCES_ALL.append(CREATE_OMICS_RUN)
RESOURCES_ALL.extend(OMICS_RUN_ALL)

RESOURCES_ALL_WITH_DESC[CREATE_OMICS_RUN] = 'Create Omics workflow runs on this environment'
RESOURCES_ALL_WITH_DESC[DELETE_OMICS_RUN] = 'Permission to delete Omics workflow runs'
