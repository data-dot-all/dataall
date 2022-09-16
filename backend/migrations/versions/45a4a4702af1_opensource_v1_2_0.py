"""opensource_v1.2.0

Revision ID: 45a4a4702af1
Revises: ec6ab02aa0cc
Create Date: 2022-09-15 17:53:13.455441

"""
from alembic import op
from sqlalchemy.dialects import postgresql
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '45a4a4702af1'
down_revision = 'bc6ff74a16bc'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('datapipeline', 'devStages')
    op.drop_column('datapipeline', 'inputDatasetUri')
    op.drop_column('datapipeline', 'outputDatasetUri')

    op.create_table(
        'datapipelineenvironments',
        sa.Column('label', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('owner', sa.String(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=True),
        sa.Column('updated', sa.DateTime(), nullable=True),
        sa.Column('deleted', sa.DateTime(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('envPipelineUri', sa.String(), nullable=False),
        sa.Column('environmentUri', sa.String(), nullable=False),
        sa.Column('environmentLabel', sa.String(), nullable=False),
        sa.Column('pipelineUri', sa.String(), nullable=False),
        sa.Column('pipelineLabel', sa.String(), nullable=False),
        sa.Column('stage', sa.String(), nullable=False),
        sa.Column('order', sa.Integer, nullable=False),
        sa.Column('region', sa.String(), nullable=False),
        sa.Column('AwsAccountId', sa.String(), nullable=False),
        sa.Column('samlGroupName', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('envPipelineUri'),
    )
    pass


def downgrade():
    op.add_column(
        'datapipeline', sa.Column('inputDatasetUri', sa.String(), nullable=True)
    )
    op.add_column(
        'datapipeline', sa.Column('outputDatasetUri', sa.String(), nullable=True)
    )
    op.add_column(
        'datapipeline', sa.Column('devStages', postgresql.ARRAY(sa.String()), nullable=True)
    )
    op.drop_table('datapipelineenvironments')
    pass
