"""add_omics_module

Revision ID: 67d081ab0814
Revises: 458572580709
Create Date: 2024-05-17 07:39:42.882105

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '67d081ab0814'
down_revision = '458572580709'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'omics_workflow',
        sa.Column('workflowUri', sa.VARCHAR(), nullable=False),
        sa.Column('arn', sa.VARCHAR(), nullable=False),
        sa.Column('id', sa.VARCHAR(), nullable=False),
        sa.Column('type', sa.VARCHAR(), nullable=False),
        sa.Column('environmentUri', sa.VARCHAR(), nullable=False),
        sa.Column('label', sa.VARCHAR(), nullable=False),
        sa.Column('owner', sa.VARCHAR(), nullable=False),
        sa.Column('name', sa.VARCHAR(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=True),
        sa.Column('updated', sa.DateTime(), nullable=True),
        sa.Column('deleted', sa.DateTime(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.PrimaryKeyConstraint('workflowUri', name='omics_workflow_pkey'),
    )

    op.create_table(
        'omics_run',
        sa.Column('runUri', sa.VARCHAR(), nullable=False),
        sa.Column('organizationUri', sa.VARCHAR(), nullable=False),
        sa.Column('environmentUri', sa.VARCHAR(), nullable=False),
        sa.Column('workflowUri', sa.VARCHAR(), nullable=False),
        sa.Column('parameterTemplate', sa.VARCHAR(), nullable=False),
        sa.Column('SamlAdminGroupName', sa.VARCHAR(), nullable=False),
        sa.Column('outputUri', sa.VARCHAR(), nullable=False),
        sa.Column('outputDatasetUri', sa.VARCHAR(), nullable=False),
        sa.Column('label', sa.VARCHAR(), nullable=False),
        sa.Column('owner', sa.VARCHAR(), nullable=False),
        sa.Column('name', sa.VARCHAR(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=True),
        sa.Column('updated', sa.DateTime(), nullable=True),
        sa.Column('deleted', sa.DateTime(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.PrimaryKeyConstraint('runUri', name='omics_run_pkey'),
    )


def downgrade():
    op.drop_table('omics_workflow')
    op.drop_table('omics_run')
