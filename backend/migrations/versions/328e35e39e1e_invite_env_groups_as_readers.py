"""invite_env_groups_as_readers

Revision ID: 328e35e39e1e
Revises: f2f7431c34e5
Create Date: 2024-06-18 17:00:22.910461

"""
from alembic import op
from sqlalchemy import orm
from dataall.core.environment.db.environment_models import EnvironmentGroup, Environment
from dataall.core.organizations.db.organization_repositories import OrganizationRepository
from dataall.core.organizations.services.organization_service import OrganizationService
from dataall.core.permissions.services.organization_permissions import GET_ORGANIZATION



# revision identifiers, used by Alembic.
revision = '328e35e39e1e'
down_revision = 'f2f7431c34e5'
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
        group_membership = OrganizationRepository.find_group_membership(session, [group], env_org[group.environmentUri])
        if group_membership is None:
            data = {
                'groupUri': group.groupUri,
                'permissions': [GET_ORGANIZATION],
            }
            OrganizationService.invite_group( env_org[group.environmentUri], data)


def downgrade():
    print('Downgrade not supported for this migration: invite env groups into otgs as readers.')