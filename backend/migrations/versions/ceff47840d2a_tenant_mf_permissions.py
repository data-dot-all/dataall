"""tenant_mf_permissions

Revision ID: ceff47840d2a
Revises: afcfc928c640
Create Date: 2024-08-14 09:44:13.794017

"""

from alembic import op
from sqlalchemy import orm

from dataall.core.permissions.api.enums import PermissionType
from dataall.core.permissions.db.permission.permission_models import Permission
from dataall.core.permissions.db.tenant.tenant_models import TenantPolicyPermission
from dataall.core.permissions.services.permission_service import PermissionService
from dataall.modules.metadata_forms.services.metadata_form_permissions import MANAGE_METADATA_FORMS


# revision identifiers, used by Alembic.
revision = 'ceff47840d2a'
down_revision = '9efe5f7c69a1'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    PermissionService.save_permission(
        session,
        name=MANAGE_METADATA_FORMS,
        description='Manage metadata forms',
        permission_type=PermissionType.TENANT.name,
    )


def downgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    perm = (
        session.query(Permission)
        .filter(Permission.name == MANAGE_METADATA_FORMS, Permission.type == PermissionType.TENANT.name)
        .first()
    )
    if not perm:
        print(f'Permission {MANAGE_METADATA_FORMS} not found')
        return
    else:
        print(f'MANAGE_METADATA_FORMS permission uri= {perm.permissionUri}')
        tenant_permissions = (
            session.query(TenantPolicyPermission)
            .filter(TenantPolicyPermission.permissionUri == perm.permissionUri)
            .all()
        )
        for permission in tenant_permissions:
            session.delete(permission)
        session.delete(perm)
