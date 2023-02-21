"""
Add module's permissions to the global permissions.
Contains permissions to work with notebooks both for sagemaker notebooks and ml studio notebooks
"""

from dataall.db.permissions import (
    TENANT_ALL,
    TENANT_ALL_WITH_DESC,
    ENVIRONMENT_ALL,
    ENVIRONMENT_INVITATION_REQUEST,
    ENVIRONMENT_INVITED,
    RESOURCES_ALL_WITH_DESC,
    RESOURCES_ALL,
)

CREATE_NOTEBOOK = "CREATE_NOTEBOOK"
MANAGE_NOTEBOOKS = "MANAGE_NOTEBOOKS"

TENANT_ALL.append(MANAGE_NOTEBOOKS)
TENANT_ALL_WITH_DESC[MANAGE_NOTEBOOKS] = "Manage notebooks"

ENVIRONMENT_ALL.append(CREATE_NOTEBOOK)
ENVIRONMENT_INVITATION_REQUEST.append(CREATE_NOTEBOOK)
ENVIRONMENT_INVITED.append(CREATE_NOTEBOOK)

RESOURCES_ALL.append(CREATE_NOTEBOOK)
RESOURCES_ALL_WITH_DESC[CREATE_NOTEBOOK] = "Create notebooks on this environment"
