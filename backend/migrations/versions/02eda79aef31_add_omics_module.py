"""add_omics_module

Revision ID: 02eda79aef31
Revises: 917b923f74bd
Create Date: 2023-10-05 18:09:05.117171

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '02eda79aef31'
down_revision = '917b923f74bd'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'omics_workflow',
        sa.Column('arn', sa.VARCHAR(), nullable=False),
        sa.Column('id', sa.VARCHAR(), nullable=False),
        sa.Column('label', sa.VARCHAR(), nullable=False),
        sa.Column('owner', sa.VARCHAR(), nullable=False),
        sa.Column('name', sa.VARCHAR(), nullable=False),
        sa.Column('status', sa.VARCHAR(), nullable=False),
        sa.Column('type', sa.VARCHAR(), nullable=False),
        sa.Column('environmentUri', sa.VARCHAR(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=True),
        sa.Column('updated', sa.DateTime(), nullable=True),
        sa.Column('deleted', sa.DateTime(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.PrimaryKeyConstraint('id', name='id_pkey'),
    )

    # TODO: add omics_run table when ready

    # op.create_table(
    #     'omics_run',
    #     sa.Column('arn', sa.VARCHAR(), nullable=False),
    #     sa.Column('id', sa.VARCHAR(), nullable=False),
    #     sa.Column('label', sa.VARCHAR(), nullable=False),
    #     sa.Column('owner', sa.VARCHAR(), nullable=False),
    #     sa.Column('name', sa.VARCHAR(), nullable=False),
    #     sa.Column('status', sa.VARCHAR(), nullable=False),
    #     sa.Column('type', sa.VARCHAR(), nullable=False),
    #     sa.Column('environmentUri', sa.VARCHAR(), nullable=False),
    #     sa.Column('created', sa.DateTime(), nullable=True),
    #     sa.Column('updated', sa.DateTime(), nullable=True),
    #     sa.Column('deleted', sa.DateTime(), nullable=True),
    #     sa.Column('description', sa.String(), nullable=True),
    #     sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
    #     sa.PrimaryKeyConstraint('id', name='id_pkey'),
    # )


def downgrade():
    op.drop_table('omics_workflow')
    # op.drop_table('omics_run')
