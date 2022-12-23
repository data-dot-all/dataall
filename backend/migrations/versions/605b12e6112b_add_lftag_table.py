"""add_lftag_table

Revision ID: 605b12e6112b
Revises: 04d92886fabe
Create Date: 2022-12-23 09:33:32.564299

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base


# revision identifiers, used by Alembic.
revision = '605b12e6112b'
down_revision = '04d92886fabe'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'lftags',
        sa.Column('lftagUri', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('LFTagName', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('LFTagValues', sa.ARRAY(sa.String()), autoincrement=False, nullable=False),
        sa.Column('teams', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column(
            'created', postgresql.TIMESTAMP(), autoincrement=False, nullable=True
        ),
        sa.Column(
            'updated', postgresql.TIMESTAMP(), autoincrement=False, nullable=True
        ),
        sa.Column(
            'deleted', postgresql.TIMESTAMP(), autoincrement=False, nullable=True
        ),
        sa.PrimaryKeyConstraint('consumptionRoleUri', name='consumptionRoleUri_pkey'),
    )


def downgrade():
    op.drop_table('lftags')
