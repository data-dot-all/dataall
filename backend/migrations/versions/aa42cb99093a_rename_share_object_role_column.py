"""rename_share_object_role_column

Revision ID: aa42cb99093a
Revises: b2ca24b72ca4
Create Date: 2024-08-07 09:59:57.691419

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'aa42cb99093a'
down_revision = 'b2ca24b72ca4'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('share_object', 'principalIAMRoleName', nullable=True, new_column_name='principalRoleName')


def downgrade():
    op.alter_column('share_object', 'principalRoleName', nullable=True, new_column_name='principalIAMRoleName')
