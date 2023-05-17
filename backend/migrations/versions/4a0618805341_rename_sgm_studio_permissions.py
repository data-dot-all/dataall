"""rename_sgm_studio_permissions

Revision ID: 4a0618805341
Revises: 5fc49baecea4
Create Date: 2023-05-17 13:39:00.974409

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Boolean, Column, String, orm, and_, or_

from dataall.db.api.permission import Permission as PermissionService
from dataall.db.models import (
    Permission,
    PermissionType,
    TenantPolicy,
    TenantPolicyPermission
)
from dataall.modules.notebooks.services.notebook_permissions import MANAGE_NOTEBOOKS
from dataall.modules.mlstudio.services.mlstudio_permissions import (
    MANAGE_SGMSTUDIO_USERS,
)


# revision identifiers, used by Alembic.
revision = '4a0618805341'
down_revision = '5fc49baecea4'
branch_labels = None
depends_on = None


def upgrade():
    """
    The script does the following migration:
        1) create missing permissions MANAGE_SGMSTUDIO_USERS from MANAGE_NOTEBOOKS tenant permission
        2) Rename SageMaker Studio permissions from SGMSTUDIO_NOTEBOOK to SGMSTUDIO_USER
        3) Rename sagemaker_studio_user_profile column names
    """
    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)

        print("Creating new permission MANAGE_SGMSTUDIO_USERS to distinguish from MANAGE_NOTEBOOKS...")
        #todo: right now this migration fails

        # PermissionService.init_permissions(session)
        #
        # manage_notebooks = PermissionService.get_permission_by_name(
        #     session, MANAGE_NOTEBOOKS, PermissionType.TENANT.name
        # )
        # manage_mlstudio = PermissionService.get_permission_by_name(
        #     session, MANAGE_SGMSTUDIO_USERS, PermissionType.TENANT.name
        # )
        #
        # tenant_permissions = (
        #     session.query(TenantPolicyPermission)
        #     .filter(TenantPolicyPermission.permission == manage_notebooks.permissionUri)
        #     .all()
        # )
        #
        # for permission in tenant_permissions:
        #     session.add(TenantPolicyPermission(
        #         sid=permission.sid,
        #         permissionUri=manage_mlstudio.permissionUri,
        #     ))
        # session.commit()

        print("Renaming SageMaker Studio permissions from SGMSTUDIO_NOTEBOOK to SGMSTUDIO_USER...")
        old_permissions = [
            'CREATE_SGMSTUDIO_NOTEBOOK',
            'LIST_ENVIRONMENT_SGMSTUDIO_NOTEBOOKS',
            'GET_SGMSTUDIO_NOTEBOOK',
            'UPDATE_SGMSTUDIO_NOTEBOOK',
            'DELETE_SGMSTUDIO_NOTEBOOK',
            'SGMSTUDIO_NOTEBOOK_URL'
        ]

        CREATE_SGMSTUDIO_USER = 'CREATE_SGMSTUDIO_USER'
        LIST_ENVIRONMENT_SGMSTUDIO_USERS = 'LIST_ENVIRONMENT_SGMSTUDIO_USERS'

        GET_SGMSTUDIO_USER = 'GET_SGMSTUDIO_USER'
        UPDATE_SGMSTUDIO_USER = 'UPDATE_SGMSTUDIO_USER'
        DELETE_SGMSTUDIO_USER = 'DELETE_SGMSTUDIO_USER'
        SGMSTUDIO_USER_URL = 'SGMSTUDIO_USER_URL'

        NEW_PERMISSIONS = [
            CREATE_SGMSTUDIO_USER,
            LIST_ENVIRONMENT_SGMSTUDIO_USERS,
            GET_SGMSTUDIO_USER,
            UPDATE_SGMSTUDIO_USER,
            DELETE_SGMSTUDIO_USER,
            SGMSTUDIO_USER_URL
        ]
        new_permissions = {k: k for k in NEW_PERMISSIONS}
        new_permissions[CREATE_SGMSTUDIO_USER] = 'Create ML Studio profiles on this environment'

        for old, new in zip(old_permissions, list(new_permissions.items())):
            print(f"updating permission {old} to {new[0]}:{new[1]}")
            session.query(Permission).filter(Permission.name==old).update({Permission.name:new[0], Permission.description:new[1]}, synchronize_session=False)
            session.commit()

    except Exception as e:
        print(f"Failed to execute the migration script due to: {e}")


def downgrade():
    pass
