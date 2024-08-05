"""add_encryption_column_redshift_connection

Revision ID: b2ca24b72ca4
Revises: 852cdf6cf1e0
Create Date: 2024-07-31 15:52:32.597785

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2ca24b72ca4'
down_revision = '852cdf6cf1e0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'redshift_connection',
        sa.Column('encryptionType', sa.String(), nullable=True),
    )
    op.add_column(
        'redshift_connection',
        sa.Column('connectionType', sa.String(), nullable=False),
    )


def downgrade():
    op.drop_column('redshift_connection', 'encryptionType')
    op.drop_column('redshift_connection', 'connectionType')
