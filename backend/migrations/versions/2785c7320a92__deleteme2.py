"""_deleteme2

Revision ID: 2785c7320a92
Revises: eb2a6250c50a
Create Date: 2022-12-06 17:25:55.394576

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm
from dataall.db import api, models, get_engine, has_table
from dataall.db import permissions

# revision identifiers, used by Alembic.
revision = '2785c7320a92'
down_revision = 'eb2a6250c50a'
branch_labels = None
depends_on = None


def upgrade():
    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)
        print('Creating backfill consumer role permissions for environments')
        envs = api.Environment.list_all_active_environments(session=session)
        for env in envs:
            groups = api.Environment.query_all_environment_groups(
                session=session, uri=env.environmentUri, filter=None
            )
            for group in groups:
                api.ResourcePolicy.attach_resource_policy(
                    session=session,
                    resource_uri=env.environmentUri,
                    group=group.groupUri,
                    permissions=permissions.CONSUMPTION_ROLE_ALL,
                    resource_type=models.Environment.__name__,
                )
        print('Permissions created successfully')
    except Exception as e:
        print(f'Failed to init permissions due to: {e}')
    # ### end Alembic commands ###


def downgrade():
    pass
