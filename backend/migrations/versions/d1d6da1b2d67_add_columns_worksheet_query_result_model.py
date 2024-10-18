"""add_columns_worksheet_query_result_model

Revision ID: d1d6da1b2d67
Revises: d274e756f0ae
Create Date: 2024-09-10 14:34:31.492186

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd1d6da1b2d67'
down_revision = 'f87aecc36d39'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('worksheet_query_result', 'status', nullable=True)
    op.alter_column('worksheet_query_result', 'sqlBody', nullable=True)
    op.alter_column('worksheet_query_result', 'DataScannedInBytes', type_=sa.BigInteger(), nullable=True)
    op.add_column('worksheet_query_result', sa.Column('downloadLink', sa.String(), nullable=True))
    op.add_column('worksheet_query_result', sa.Column('expiresIn', sa.DateTime(), nullable=True))
    op.add_column('worksheet_query_result', sa.Column('updated', sa.DateTime(), nullable=False))
    op.add_column('worksheet_query_result', sa.Column('fileFormat', sa.String(), nullable=True))
    op.add_column('worksheet_query_result', sa.Column('worksheetQueryResultUri', sa.String(), nullable=False))
    op.drop_constraint('AthenaQueryId', 'worksheet_query_result', type_='primary')
    op.create_primary_key('worksheet_query_result_pkey', 'worksheet_query_result', ['worksheetQueryResultUri'])
    op.alter_column('worksheet_query_result', 'AthenaQueryId', nullable=False)
    op.drop_column('worksheet_query_result', 'queryType')


def downgrade():
    op.add_column('worksheet_query_result', sa.Column('queryType', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_constraint('worksheet_query_result_pkey', 'worksheet_query_result', type_='primary')
    op.create_primary_key('AthenaQueryId', 'worksheet_query_result', ['AthenaQueryId'])
    op.drop_column('worksheet_query_result', 'worksheetQueryResultUri')
    op.drop_column('worksheet_query_result', 'fileFormat')
    op.drop_column('worksheet_query_result', 'updated')
    op.drop_column('worksheet_query_result', 'expiresIn')
    op.drop_column('worksheet_query_result', 'downloadLink')
    op.alter_column('worksheet_query_result', 'DataScannedInBytes', type_=sa.Integer(), nullable=True)
    op.alter_column('worksheet_query_result', 'sqlBody', nullable=False)
    op.alter_column('worksheet_query_result', 'status', nullable=False)
