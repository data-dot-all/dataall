"""add_share_object_permissions

Revision ID: c215903b780c
Revises: 9efe5f7c69a1
Create Date: 2024-08-08 16:19:25.731721

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c215903b780c'
down_revision = '9efe5f7c69a1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'share_object', sa.Column('permissions', postgresql.ARRAY(sa.String()), nullable=False, server_default='{Read}')
    )


def downgrade():
    op.drop_column('share_object', 'permissions')
