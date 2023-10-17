"""add_omics_runs

Revision ID: 9337b882dbb8
Revises: 02eda79aef31
Create Date: 2023-10-17 10:51:53.224705

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '9337b882dbb8'
down_revision = '02eda79aef31'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'omics_run',
        sa.Column('runUri', sa.VARCHAR(), nullable=False),
        sa.Column('organizationUri', sa.VARCHAR(), nullable=False),
        sa.Column('environmentUri', sa.VARCHAR(), nullable=False),
        sa.Column('region', sa.VARCHAR(), nullable=False),
        sa.Column('AwsAccountId', sa.VARCHAR(), nullable=False),
        sa.Column('workflowId', sa.VARCHAR(), nullable=False),
        sa.Column('parameterTemplate', sa.VARCHAR(), nullable=False),
        sa.Column('outputUri', sa.VARCHAR(), nullable=False),
        sa.Column('label', sa.VARCHAR(), nullable=False),
        sa.Column('owner', sa.VARCHAR(), nullable=False),
        sa.Column('name', sa.VARCHAR(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=True),
        sa.Column('updated', sa.DateTime(), nullable=True),
        sa.Column('deleted', sa.DateTime(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.PrimaryKeyConstraint('runUri', name='id_pkey'),
    )

def downgrade():
    op.drop_table('omics_run')
