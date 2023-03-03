"""add_lftag_shareobject_table

Revision ID: 87713017ce9f
Revises: 72de510b8ba3
Create Date: 2023-01-12 11:48:53.921682

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '87713017ce9f'
down_revision = '72de510b8ba3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'lftag_share_object',
        sa.Column('lftagShareUri', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('lfTagKey', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('lfTagValue', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('environmentUri', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('groupUri', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('principalIAMRoleName', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('principalId', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('principalType', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('status', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('owner', sa.String(), nullable=False),
        sa.Column('created', sa.DateTime(), autoincrement=False, nullable=True),
        sa.Column('updated', sa.DateTime(), autoincrement=False, nullable=True),
        sa.Column('deleted', sa.DateTime(), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint('lftagShareUri'),
    )


def downgrade():
    op.drop_table('lftag_share_object')
