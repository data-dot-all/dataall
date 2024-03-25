"""add_dataallManaged_roles

Revision ID: 194608b1ff7f
Revises: af702716568f
Create Date: 2024-02-29 23:14:07.686581

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '194608b1ff7f'
down_revision = 'af702716568f'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'consumptionrole',
        sa.Column('dataallManaged', sa.Boolean(), nullable=False, server_default=sa.sql.expression.true()),
    )


def downgrade():
    op.drop_column('consumptionrole', 'dataallManaged')
