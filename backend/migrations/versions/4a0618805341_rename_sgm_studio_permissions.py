"""rename_sgm_studio_permissions

Revision ID: 4a0618805341
Revises: 92bdf9efb1aa
Create Date: 2023-05-17 13:39:00.974409

"""

from alembic import op
from sqlalchemy import String, orm, and_

from dataall.core.permissions.services.permission_service import PermissionService
from dataall.core.permissions.db.permission.permission_models import Permission
from dataall.core.permissions.api.enums import PermissionType
from dataall.core.permissions.db.tenant.tenant_models import TenantPolicyPermission
from dataall.modules.notebooks.services.notebook_permissions import MANAGE_NOTEBOOKS
from dataall.modules.mlstudio.services.mlstudio_permissions import (
    MANAGE_SGMSTUDIO_USERS,
)

# revision identifiers, used by Alembic.
revision = '4a0618805341'
down_revision = '92bdf9efb1aa'
branch_labels = None
depends_on = None

# Define constants
CREATE_SGMSTUDIO_NOTEBOOK = 'CREATE_SGMSTUDIO_NOTEBOOK'
LIST_ENVIRONMENT_SGMSTUDIO_NOTEBOOKS = 'LIST_ENVIRONMENT_SGMSTUDIO_NOTEBOOKS'

GET_SGMSTUDIO_NOTEBOOK = 'GET_SGMSTUDIO_NOTEBOOK'
UPDATE_SGMSTUDIO_NOTEBOOK = 'UPDATE_SGMSTUDIO_NOTEBOOK'
DELETE_SGMSTUDIO_NOTEBOOK = 'DELETE_SGMSTUDIO_NOTEBOOK'
SGMSTUDIO_NOTEBOOK_URL = 'SGMSTUDIO_NOTEBOOK_URL'
RUN_ATHENA_QUERY = 'RUN_ATHENA_QUERY'
CREATE_SHARE_OBJECT = 'CREATE_SHARE_OBJECT'

OLD_PERMISSIONS = [
    CREATE_SGMSTUDIO_NOTEBOOK,
    LIST_ENVIRONMENT_SGMSTUDIO_NOTEBOOKS,
    GET_SGMSTUDIO_NOTEBOOK,
    UPDATE_SGMSTUDIO_NOTEBOOK,
    DELETE_SGMSTUDIO_NOTEBOOK,
    SGMSTUDIO_NOTEBOOK_URL,
    RUN_ATHENA_QUERY,
    CREATE_SHARE_OBJECT,
]
old_permissions = {k: k for k in OLD_PERMISSIONS}
old_permissions[CREATE_SGMSTUDIO_NOTEBOOK] = 'Create ML Studio profiles on this environment'
old_permissions[CREATE_SHARE_OBJECT] = 'Request datasets access for this environment'

CREATE_SGMSTUDIO_USER = 'CREATE_SGMSTUDIO_USER'
LIST_ENVIRONMENT_SGMSTUDIO_USERS = 'LIST_ENVIRONMENT_SGMSTUDIO_USERS'

GET_SGMSTUDIO_USER = 'GET_SGMSTUDIO_USER'
UPDATE_SGMSTUDIO_USER = 'UPDATE_SGMSTUDIO_USER'
DELETE_SGMSTUDIO_USER = 'DELETE_SGMSTUDIO_USER'
SGMSTUDIO_USER_URL = 'SGMSTUDIO_USER_URL'
RUN_ATHENA_QUERY = 'RUN_ATHENA_QUERY'

NEW_PERMISSIONS = [
    CREATE_SGMSTUDIO_USER,
    LIST_ENVIRONMENT_SGMSTUDIO_USERS,
    GET_SGMSTUDIO_USER,
    UPDATE_SGMSTUDIO_USER,
    DELETE_SGMSTUDIO_USER,
    SGMSTUDIO_USER_URL,
    RUN_ATHENA_QUERY,
    CREATE_SHARE_OBJECT,
]
new_permissions = {k: k for k in NEW_PERMISSIONS}
new_permissions[CREATE_SGMSTUDIO_USER] = 'Create SageMaker Studio users on this environment'
new_permissions[RUN_ATHENA_QUERY] = 'Run Worksheet Athena queries on this environment'
new_permissions[CREATE_SHARE_OBJECT] = 'Create dataset Share requests for this environment'


def upgrade():
    """
    The script does the following migration:
        1) create missing permissions MANAGE_SGMSTUDIO_USERS from MANAGE_NOTEBOOKS tenant permission
        2) Rename SageMaker Studio permissions from SGMSTUDIO_NOTEBOOK to SGMSTUDIO_USER
        and add description to RUN_ATHENA_QUERY and create share object
        3) Rename sagemaker_studio_user_profile column names
    """
    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)

        print('Creating new permission MANAGE_SGMSTUDIO_USERS to distinguish from MANAGE_NOTEBOOKS...')

        manage_mlstudio_permission = PermissionService.save_permission(
            session=session,
            name=MANAGE_SGMSTUDIO_USERS,
            description='Allow MANAGE_SGMSTUDIO_USERS',
            permission_type=PermissionType.TENANT.name,
        )
        session.commit()
        print(f'manage_mlstudio_permission_uri = {manage_mlstudio_permission.permissionUri}')
        manage_notebooks_permission = (
            session.query(Permission)
            .filter(and_(Permission.name == MANAGE_NOTEBOOKS, Permission.type == PermissionType.TENANT.name))
            .first()
        )
        print(f'manage_notebooks_permission_uri = {manage_notebooks_permission.permissionUri}')
        tenant_permissions = (
            session.query(TenantPolicyPermission)
            .filter(TenantPolicyPermission.permissionUri == manage_notebooks_permission.permissionUri)
            .all()
        )
        for permission in tenant_permissions:
            print(permission.permissionUri)
            existing_tenant_permissions = (
                session.query(TenantPolicyPermission)
                .filter(
                    and_(
                        TenantPolicyPermission.permissionUri == manage_mlstudio_permission.permissionUri,
                        TenantPolicyPermission.sid == permission.sid,
                    )
                )
                .first()
            )

            if existing_tenant_permissions:
                print(f'Permission already exists {existing_tenant_permissions.permissionUri}, skipping...')
            else:
                print('Permission does not exist, adding it...')
                session.add(
                    TenantPolicyPermission(
                        sid=permission.sid,
                        permissionUri=manage_mlstudio_permission.permissionUri,
                    )
                )

        session.commit()

        print('Renaming SageMaker Studio permissions from SGMSTUDIO_NOTEBOOK to SGMSTUDIO_USER...')

        for old, new in zip(list(old_permissions.items()), list(new_permissions.items())):
            print(f'Updating permission table {old[0]} to {new[0]}, description:{new[1]}')
            session.query(Permission).filter(Permission.name == old[0]).update(
                {Permission.name: new[0], Permission.description: new[1]}, synchronize_session=False
            )
            session.commit()

        print('Renaming columns of sagemaker_studio_user_profile...')
        op.alter_column(
            'sagemaker_studio_user_profile',
            'sagemakerStudioUserProfileUri',
            nullable=False,
            new_column_name='sagemakerStudioUserUri',
            existing_type=String,
        )
        op.alter_column(
            'sagemaker_studio_user_profile',
            'sagemakerStudioUserProfileStatus',
            nullable=False,
            new_column_name='sagemakerStudioUserStatus',
            existing_type=String,
        )
        op.alter_column(
            'sagemaker_studio_user_profile',
            'sagemakerStudioUserProfileName',
            nullable=False,
            new_column_name='sagemakerStudioUserName',
            existing_type=String,
        )
        op.alter_column(
            'sagemaker_studio_user_profile',
            'sagemakerStudioUserProfileNameSlugify',
            nullable=False,
            new_column_name='sagemakerStudioUserNameSlugify',
            existing_type=String,
        )
    except Exception as e:
        print(f'Failed to execute the migration script due to: {e}')


def downgrade():
    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)

        print('Dropping new permission added to MANAGE_SGMSTUDIO_USERS to distinguish from MANAGE_NOTEBOOKS...')
        manage_mlstudio_permission = (
            session.query(Permission)
            .filter(and_(Permission.name == MANAGE_SGMSTUDIO_USERS, Permission.type == PermissionType.TENANT.name))
            .first()
        )
        print(f'manage_mlstudio_permission_uri = {manage_mlstudio_permission.permissionUri}')
        tenant_permissions = (
            session.query(TenantPolicyPermission)
            .filter(TenantPolicyPermission.permissionUri == manage_mlstudio_permission.permissionUri)
            .delete()
        )

        manage_mlstudio_permission = (
            session.query(Permission)
            .filter(and_(Permission.name == MANAGE_SGMSTUDIO_USERS, Permission.type == PermissionType.TENANT.name))
            .delete()
        )
        session.commit()

        print('Renaming SageMaker Studio permissions from SGMSTUDIO_USER to SGMSTUDIO_NOTEBOOK...')
        for old, new in zip(list(old_permissions.items()), list(new_permissions.items())):
            print(f'Updating permission table {new[0]} to name={old[0]}, description={old[1]}')
            session.query(Permission).filter(Permission.name == new[0]).update(
                {Permission.name: old[0], Permission.description: old[1]}, synchronize_session=False
            )
            session.commit()

        print('Renaming columns of sagemaker_studio_user_profile...')
        op.alter_column(
            'sagemaker_studio_user_profile',
            'sagemakerStudioUserUri',
            nullable=False,
            new_column_name='sagemakerStudioUserProfileUri',
            existing_type=String,
        )
        op.alter_column(
            'sagemaker_studio_user_profile',
            'sagemakerStudioUserStatus',
            nullable=False,
            new_column_name='sagemakerStudioUserProfileStatus',
            existing_type=String,
        )
        op.alter_column(
            'sagemaker_studio_user_profile',
            'sagemakerStudioUserName',
            nullable=False,
            new_column_name='sagemakerStudioUserProfileName',
            existing_type=String,
        )
        op.alter_column(
            'sagemaker_studio_user_profile',
            'sagemakerStudioUserNameSlugify',
            nullable=False,
            new_column_name='sagemakerStudioUserProfileNameSlugify',
            existing_type=String,
        )

    except Exception as e:
        print(f'Failed to execute the migration script due to: {e}')
