"""add_cascade_column_keyvaluetags

Revision ID: d922057f0d91
Revises: 45a4a4702af1
Create Date: 2022-11-09 10:23:36.279140

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd922057f0d91'
down_revision = '45a4a4702af1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('keyvaluetag', sa.Column('cascade', sa.Boolean()))
    pass


def downgrade():
    op.drop_column('keyvaluetag', 'cascade')
    pass
