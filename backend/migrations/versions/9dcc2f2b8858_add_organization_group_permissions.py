"""add_organization_group_permissions

Revision ID: 9dcc2f2b8858
Revises: 194608b1ff7f
Create Date: 2024-04-11 10:34:06.827154

"""

from alembic import op
from sqlalchemy import orm
from dataall.core.organizations.db.organization_models import OrganizationGroup, Organization
from dataall.core.permissions.api.enums import PermissionType
from dataall.core.permissions.services.permission_service import PermissionService
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.organization_permissions import (
    INVITE_ORGANIZATION_GROUP,
    REMOVE_ORGANIZATION_GROUP,
)

# revision identifiers, used by Alembic.
revision = '9dcc2f2b8858'
down_revision = '194608b1ff7f'
branch_labels = None
depends_on = None


def get_session():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    return session


def upgrade():
    session = get_session()
    print('Adding organization group permissions...')
    invite_permission = PermissionService.save_permission(
        session=session,
        name=INVITE_ORGANIZATION_GROUP,
        description='INVITE_ORGANIZATION_GROUP',
        permission_type=PermissionType.RESOURCE.name,
    )
    remove_permission = PermissionService.save_permission(
        session=session,
        name=REMOVE_ORGANIZATION_GROUP,
        description='REMOVE_ORGANIZATION_GROUP',
        permission_type=PermissionType.RESOURCE.name,
    )
    all_org_groups = session.query(OrganizationGroup).all()
    for org_group in all_org_groups:
        ResourcePolicyService.attach_resource_policy(
            session=session,
            group=org_group.groupUri,
            resource_uri=org_group.organizationUri,
            permissions=[INVITE_ORGANIZATION_GROUP, REMOVE_ORGANIZATION_GROUP],
            resource_type=Organization.__name__,
        )


def downgrade():
    # No downgrade. It's a bugfix
    print('Downgrade not supported for this migration: add_organization_group_permissions.')
