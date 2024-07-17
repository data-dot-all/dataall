"""describe_changes_shortly

Revision ID: 9efe5f7c69a1
Revises: 797dd1012be1
Create Date: 2024-07-17 11:05:26.077658

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9efe5f7c69a1'
down_revision = '797dd1012be1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'data_filter',
        sa.Column('label', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('owner', sa.String(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=True),
        sa.Column('updated', sa.DateTime(), nullable=True),
        sa.Column('deleted', sa.DateTime(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('filterUri', sa.String(), nullable=False),
        sa.Column('tableUri', sa.String(), nullable=False),
        sa.Column('filterType', sa.String(), nullable=False),
        sa.Column('includedCols', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('rowExpression', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['tableUri'], ['dataset_table.tableUri'], name='data_filter_tableUri_fkey'),
        sa.PrimaryKeyConstraint('filterUri'),
    )

    op.add_column('share_object_item', sa.Column('dataFilters', postgresql.ARRAY(sa.String()), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    op.drop_column('share_object_item', 'dataFilters')
    op.drop_table('data_filter')
    # ### end Alembic commands ###
