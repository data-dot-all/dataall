"""
Add module's permissions to the global permissions.
Contains permissions for sagemaker ML Studio
There are different types of permissions:
TENANT_PERMISSIONS
    Granted to the Tenant group. For each resource we should define a corresponding MANAGE_<RESOURCE> permission
ENVIRONMENT_PERMISSIONS
    Granted to any group in an environment. For each resource we should define a list of actions regarding
    that resource that are executed on the environment (e.g. List resources X in an environment)
ENVIRONMENT_INVITED_PERMISSIONS

ENVIRONMENT_INVITATION_REQUEST

RESOURCE_PERMISSION
    Granted to any group. For each resource we should define a list of all actions that can be done on the resource.
    We also need to add the permissions for the Environment resource (ENVIRONMENT_PERMISSIONS)

"""

from dataall.core.permissions.services.resources_permissions import (
    RESOURCES_ALL_WITH_DESC,
    RESOURCES_ALL,
)
from dataall.core.permissions.services.tenant_permissions import TENANT_ALL, TENANT_ALL_WITH_DESC
from dataall.core.permissions.services.environment_permissions import (
    ENVIRONMENT_ALL,
    ENVIRONMENT_INVITED,
    ENVIRONMENT_INVITATION_REQUEST,
)

# Definition of TENANT_PERMISSIONS for SageMaker ML Studio
MANAGE_SGMSTUDIO_USERS = 'MANAGE_SGMSTUDIO_USERS'

TENANT_ALL.append(MANAGE_SGMSTUDIO_USERS)
TENANT_ALL_WITH_DESC[MANAGE_SGMSTUDIO_USERS] = 'Manage SageMaker Studio users'


# Definition of ENVIRONMENT_PERMISSIONS for SageMaker ML Studio
CREATE_SGMSTUDIO_USER = 'CREATE_SGMSTUDIO_USER'


ENVIRONMENT_ALL.append(CREATE_SGMSTUDIO_USER)
ENVIRONMENT_INVITED.append(CREATE_SGMSTUDIO_USER)
ENVIRONMENT_INVITATION_REQUEST.append(CREATE_SGMSTUDIO_USER)

# Definition of RESOURCE_PERMISSIONS for SageMaker ML Studio
GET_SGMSTUDIO_USER = 'GET_SGMSTUDIO_USER'
UPDATE_SGMSTUDIO_USER = 'UPDATE_SGMSTUDIO_USER'
DELETE_SGMSTUDIO_USER = 'DELETE_SGMSTUDIO_USER'
SGMSTUDIO_USER_URL = 'SGMSTUDIO_USER_URL'

SGMSTUDIO_USER_ALL = [
    GET_SGMSTUDIO_USER,
    UPDATE_SGMSTUDIO_USER,
    DELETE_SGMSTUDIO_USER,
    SGMSTUDIO_USER_URL,
]

RESOURCES_ALL.extend(SGMSTUDIO_USER_ALL)
RESOURCES_ALL.append(CREATE_SGMSTUDIO_USER)


RESOURCES_ALL_WITH_DESC[GET_SGMSTUDIO_USER] = 'General permission to get a SageMaker Studio user'
RESOURCES_ALL_WITH_DESC[UPDATE_SGMSTUDIO_USER] = 'Permission to get a SageMaker Studio user'
RESOURCES_ALL_WITH_DESC[DELETE_SGMSTUDIO_USER] = 'Permission to delete a SageMaker Studio user'
RESOURCES_ALL_WITH_DESC[SGMSTUDIO_USER_URL] = 'Permission to generate the URL for a SageMaker Studio user'
RESOURCES_ALL_WITH_DESC[CREATE_SGMSTUDIO_USER] = 'Create SageMaker Studio users on this environment'
