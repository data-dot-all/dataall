"""add_consumption_roles

Revision ID: 04d92886fabe
Revises: d922057f0d91
Create Date: 2022-11-29 10:57:27.641565

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '04d92886fabe'
down_revision = 'd922057f0d91'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'consumptionrole',
        sa.Column('consumptionRoleUri', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('consumptionRoleName', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('environmentUri', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('groupUri', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('IAMRoleName', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('IAMRoleArn', sa.VARCHAR(), autoincrement=False, nullable=False),
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
    op.drop_table('consumptionrole')
