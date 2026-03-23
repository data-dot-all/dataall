"""add_permissions_boundary_to_environment

Revision ID: a4f8b2c1d3e5
Revises: 2258cd8d6e9f
Create Date: 2024-05-01 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a4f8b2c1d3e5'
down_revision = '2258cd8d6e9f'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('environment', sa.Column('PermissionsBoundaryPolicyArn', sa.String(), nullable=True))


def downgrade():
    op.drop_column('environment', 'PermissionsBoundaryPolicyArn')
