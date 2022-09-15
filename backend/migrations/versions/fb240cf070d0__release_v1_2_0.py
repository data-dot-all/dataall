"""_release_v1.2.0

Revision ID: fb240cf070d0
Revises: 652b83e1065c
Create Date: 2022-09-15 15:10:53.506962

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import Column, TIMESTAMP, INTEGER, VARCHAR, NVARCHAR


# revision identifiers, used by Alembic.
revision = 'fb240cf070d0'
down_revision = '652b83e1065c'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('datapipeline', 'devStages')
    op.drop_column('datapipeline', 'inputDatasetUri')
    op.drop_column('datapipeline', 'outputDatasetUri')

    op.create_table(
        'datapipelineenvironments',
        Column('envPipelineUri', VARCHAR(50), primary_key=True),
        Column('environmentUri', VARCHAR(50), nullable=False),
        Column('environmentLabel', VARCHAR(50), nullable=False),
        Column('pipelineUri', VARCHAR(50), nullable=False),
        Column('pipelineLabel', VARCHAR(50), nullable=False),
        Column('stage', VARCHAR(50), nullable=False),
        Column('order', INTEGER, nullable=False),
        Column('region', VARCHAR(50), nullable=False),
        Column('AwsAccountId', VARCHAR(50), nullable=False),
        Column('samlGroupName', VARCHAR(50), nullable=False),
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
