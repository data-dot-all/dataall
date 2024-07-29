"""drop_share_object_item_s3_columns

Revision ID: 6adce90ab470
Revises: 5cdcf6cc1d73
Create Date: 2024-06-05 08:27:05.393712

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6adce90ab470'
down_revision = '5cdcf6cc1d73'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('share_object_item', 'S3AccessPointName')
    op.drop_column('share_object_item', 'GlueTableName')
    op.drop_column('share_object_item', 'GlueDatabaseName')


def downgrade():
    op.add_column('share_object_item', sa.Column('GlueDatabaseName', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('share_object_item', sa.Column('GlueTableName', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('share_object_item', sa.Column('S3AccessPointName', sa.VARCHAR(), autoincrement=False, nullable=True))
