"""
Add module's permissions to the global permissions.
Contains permissions for sagemaker notebooks
"""

from dataall.core.permissions.services.resources_permissions import (
    RESOURCES_ALL_WITH_DESC,
    RESOURCES_ALL,
)

from dataall.core.permissions.services.environment_permissions import (
    ENVIRONMENT_INVITED,
    ENVIRONMENT_INVITATION_REQUEST,
    ENVIRONMENT_ALL,
)

from dataall.core.permissions.services.tenant_permissions import TENANT_ALL, TENANT_ALL_WITH_DESC

GET_NOTEBOOK = 'GET_NOTEBOOK'
UPDATE_NOTEBOOK = 'UPDATE_NOTEBOOK'
DELETE_NOTEBOOK = 'DELETE_NOTEBOOK'
CREATE_NOTEBOOK = 'CREATE_NOTEBOOK'
MANAGE_NOTEBOOKS = 'MANAGE_NOTEBOOKS'

NOTEBOOK_ALL = [
    GET_NOTEBOOK,
    DELETE_NOTEBOOK,
    UPDATE_NOTEBOOK,
]

ENVIRONMENT_ALL.append(CREATE_NOTEBOOK)
ENVIRONMENT_INVITED.append(CREATE_NOTEBOOK)
ENVIRONMENT_INVITATION_REQUEST.append(CREATE_NOTEBOOK)

TENANT_ALL.append(MANAGE_NOTEBOOKS)
TENANT_ALL_WITH_DESC[MANAGE_NOTEBOOKS] = 'Manage notebooks'


RESOURCES_ALL.append(CREATE_NOTEBOOK)
RESOURCES_ALL.extend(NOTEBOOK_ALL)

RESOURCES_ALL_WITH_DESC[CREATE_NOTEBOOK] = 'Create notebooks on this environment'
RESOURCES_ALL_WITH_DESC[GET_NOTEBOOK] = 'General permission to get a notebook'
RESOURCES_ALL_WITH_DESC[DELETE_NOTEBOOK] = 'Permission to delete a notebook'
RESOURCES_ALL_WITH_DESC[UPDATE_NOTEBOOK] = 'Permission to edit a notebook'
