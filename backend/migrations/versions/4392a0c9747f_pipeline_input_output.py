"""pipeline input output

Revision ID: 4392a0c9747f
Revises: e72009ab3b9a
Create Date: 2022-06-10 15:27:40.777295

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '4392a0c9747f'
down_revision = 'e72009ab3b9a'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('datapipeline', sa.Column('inputDatasetUri', sa.String(), nullable=True))
    op.add_column('datapipeline', sa.Column('outputDatasetUri', sa.String(), nullable=True))
    pass


def downgrade():
    op.drop_column('datapipeline', 'inputDatasetUri')
    op.drop_column('datapipeline', 'outputDatasetUri')
    pass
