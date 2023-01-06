"""add_lftag_permissions_table

Revision ID: 72de510b8ba3
Revises: 605b12e6112b
Create Date: 2023-01-04 14:43:28.815230

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import String

# revision identifiers, used by Alembic.
revision = '72de510b8ba3'
down_revision = '605b12e6112b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'lftagpermissions',
        sa.Column('tagPermissionUri', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('SamlGroupName', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('environmentUri', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('environmentLabel', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('awsAccount', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('tagKey', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('tagValues', sa.VARCHAR(), autoincrement=False, nullable=False),
    )

    op.add_column('dataset', sa.Column('lfTagKey', postgresql.ARRAY(String), nullable=True))
    op.add_column('dataset', sa.Column('lfTagValue', postgresql.ARRAY(String), nullable=True))


def downgrade():
    op.drop_table('lftagpermissions')

    op.drop_column('dataset', 'lfTagKey')
    op.drop_column('dataset', 'lfTagValue')
