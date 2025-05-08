"""merging disjoint heads

Revision ID: 0d1653ee4dc3
Revises: 77c3f1b2bec8, ba2da94739ab
Create Date: 2025-05-08 14:07:07.096840

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0d1653ee4dc3'
down_revision = ('77c3f1b2bec8', 'ba2da94739ab')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
