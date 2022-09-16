"""opensource_v1.2.0

Revision ID: 45a4a4702af1
Revises: ec6ab02aa0cc
Create Date: 2022-09-15 17:53:13.455441

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import Column, TIMESTAMP, INTEGER, VARCHAR, NVARCHAR
from dataall.db import get_engine, has_table, create_schema_if_not_exists


# revision identifiers, used by Alembic.
revision = '45a4a4702af1'
down_revision = 'bc6ff74a16bc'
branch_labels = None
depends_on = None


def upgrade():
    print('Open-source v_1.2.0')
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
