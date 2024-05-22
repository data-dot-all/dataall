"""backfill_get_org_permissions

Revision ID: 11b716ddb036
Revises: 458572580709
Create Date: 2024-05-22 17:06:34.441667

"""

from alembic import op
from sqlalchemy import orm
from dataall.core.organizations.db.organization_models import Organization
from dataall.core.environment.db.environment_models import EnvironmentGroup, Environment
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.core.permissions.services.organization_permissions import GET_ORGANIZATION


# revision identifiers, used by Alembic.
revision = '11b716ddb036'
down_revision = '458572580709'
branch_labels = None
depends_on = None


def get_session():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    return session


def upgrade():
    session = get_session()
    print('Adding GET_ORGANIZATION permissions for all environment groups...')
    all_env_groups = session.query(EnvironmentGroup).all()
    envs_list = session.query(Environment).all()
    env_org = {}
    for e in envs_list:
        env_org[e.environmentUri] = e.organizationUri

    for group in all_env_groups:
        ResourcePolicyService.attach_resource_policy(
            session=session,
            group=group.groupUri,
            resource_uri=env_org[group.environmentUri],
            permissions=[GET_ORGANIZATION],
            resource_type=Organization.__name__,
        )


def downgrade():
    print('Downgrade not supported for this migration: backfill_get_org_permissions.')
