"""add_share_object_permissions

Revision ID: c215903b780c
Revises: aa42cb99093a
Create Date: 2024-08-08 16:19:25.731721

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c215903b780c'
down_revision = 'aa42cb99093a'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('share_object', sa.Column('permissions', postgresql.ARRAY(sa.String()), nullable=False))


def downgrade():
    op.drop_column('share_object', 'permissions')
