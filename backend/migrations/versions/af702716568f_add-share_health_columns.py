"""_describe_changes_shortly

Revision ID: af702716568f
Revises: f6cd4ba7dd8d
Create Date: 2024-02-07 09:44:47.679798

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'af702716568f'
down_revision = 'f6cd4ba7dd8d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('share_object_item', sa.Column('healthStatus', sa.String(), nullable=True))
    op.add_column('share_object_item', sa.Column('healthMessage', sa.String(), nullable=True))
    op.add_column('share_object_item', sa.Column('lastVerificationTime', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    op.drop_column('share_object_item', 'lastVerificationTime')
    op.drop_column('share_object_item', 'healthMessage')
    op.drop_column('share_object_item', 'healthStatus')
    # ### end Alembic commands ###
