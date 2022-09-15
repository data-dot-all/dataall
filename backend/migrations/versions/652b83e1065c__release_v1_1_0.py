"""_release_v1.1.0

Revision ID: 652b83e1065c
Revises: ada02a56cd32
Create Date: 2022-09-15 15:10:53.506962

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '652b83e1065c'
down_revision = 'bd271a2780b2'
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table('sqlpipeline', 'datapipeline')
    op.add_column(
        'datapipeline', sa.Column('devStrategy', sa.String(), nullable=True)
    )
    op.add_column(
        'datapipeline', sa.Column('devStages', postgresql.ARRAY(sa.String()), nullable=True)
    )
    op.add_column(
        'datapipeline', sa.Column('template', sa.String(), nullable=True)
    )
    op.alter_column(
        'datapipeline', 'sqlPipelineUri', new_column_name='DataPipelineUri'
    )
    op.add_column(
        'datapipeline', sa.Column('inputDatasetUri', sa.String(), nullable=True)
    )
    op.add_column(
        'datapipeline', sa.Column('outputDatasetUri', sa.String(), nullable=True)
    )

    pass


def downgrade():
    op.drop_column('datapipeline', 'inputDatasetUri')
    op.drop_column('datapipeline', 'outputDatasetUri')
    op.drop_column('datapipeline', 'devStrategy')
    op.drop_column('datapipeline', 'devStages')
    op.drop_column('datapipeline', 'template')
    op.alter_column(
        'datapipeline', 'DataPipelineUri', new_column_name='sqlPipelineUri'
    )
    op.rename_table('datapipeline', 'sqlpipeline')

    pass
