from dataall.core.permissions.services.tenant_permissions import TENANT_ALL, TENANT_ALL_WITH_DESC


MANAGE_METADATA_FORMS = 'MANAGE_METADATA_FORMS'
TENANT_ALL.append(MANAGE_METADATA_FORMS)
TENANT_ALL_WITH_DESC[MANAGE_METADATA_FORMS] = 'Manage metadata forms'
