"""_dataset_autoapproval_field

Revision ID: f6cd4ba7dd8d
Revises: 71a5f5de322f
Create Date: 2024-01-16 13:49:29.527312

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f6cd4ba7dd8d'
down_revision = '71a5f5de322f'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('dataset', sa.Column('autoApprovalEnabled', sa.Boolean(), default=False))


def downgrade():
    op.drop_column('dataset', 'autoApprovalEnabled')
