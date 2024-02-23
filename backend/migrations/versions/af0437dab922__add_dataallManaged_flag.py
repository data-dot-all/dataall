"""_add_dataallManaged_flag

Revision ID: af0437dab922
Revises: f6cd4ba7dd8d
Create Date: 2024-02-15 10:42:06.833990

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'af0437dab922'
down_revision = '6c9a8afee4e4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('consumptionrole', sa.Column('dataallManaged', sa.Boolean(), nullable=False))


def downgrade():
    op.drop_column('consumptionrole', 'dataallManaged')
