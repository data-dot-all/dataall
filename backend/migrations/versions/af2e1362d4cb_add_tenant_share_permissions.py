"""add_tenant_share_permissions

Revision ID: af2e1362d4cb
Revises: 49c6b18ed814
Create Date: 2024-11-18 15:23:08.215870

"""

from alembic import op
from sqlalchemy import orm
from sqlalchemy.sql import and_
from dataall.core.permissions.services.permission_service import PermissionService
from dataall.core.permissions.db.tenant.tenant_models import TenantPolicy
from dataall.core.permissions.db.tenant.tenant_policy_repositories import TenantPolicyRepository
from dataall.modules.shares_base.services.share_permissions import MANAGE_SHARES
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService

# revision identifiers, used by Alembic.
revision = 'af2e1362d4cb'
down_revision = '49c6b18ed814'
branch_labels = None
depends_on = None
TENANT_NAME = 'dataall'


def upgrade():
    from dataall.core.permissions.db.permission.permission_models import Permission, PermissionType

    # Ensure all permissions including MANAGE_SHARES are created in the db
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    PermissionService.init_permissions(session)

    # listTenantGroups
    tenant_groups = (
        session.query(
            TenantPolicy.principalId.label('name'),
            TenantPolicy.principalId.label('groupUri'),
        )
        .filter(
            and_(
                TenantPolicy.principalType == 'GROUP',
                TenantPolicy.principalId != 'DAAdministrators',
            )
        )
        .all()
    )
    # updateGroupTenantPermissions and add MANAGE_SHARES
    for group in tenant_groups:
        policy = TenantPolicyRepository.find_tenant_policy(
            session=session,
            group_uri=group.groupUri,
            tenant_name=TENANT_NAME,
        )
        already_associated = TenantPolicyRepository.has_group_tenant_permission(
            session,
            group_uri=group.groupUri,
            permission_name=MANAGE_SHARES,
            tenant_name=TENANT_NAME,
        )

        if not already_associated:
            TenantPolicyService.associate_permission_to_tenant_policy(session, policy, MANAGE_SHARES)


def downgrade():
    pass
