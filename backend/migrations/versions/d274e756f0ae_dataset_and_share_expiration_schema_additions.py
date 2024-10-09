"""schema_for_share_expiration

Revision ID: d274e756f0ae
Revises: 797dd1012be1
Create Date: 2024-07-18 14:25:20.728900

"""

import os
from alembic import op
import sqlalchemy as sa
from dataall.base.db import get_engine, has_column

# revision identifiers, used by Alembic.
revision = 'd274e756f0ae'
down_revision = 'c215903b780c'
branch_labels = None
depends_on = None

envname = os.getenv('envname', 'local')
print('ENVNAME', envname)
engine = get_engine(envname=envname).engine


def upgrade():
    print('Adding columns for share expiration')
    # Add Columns to the dataset base table
    op.add_column(
        'dataset',
        sa.Column(
            'enableExpiration', sa.Boolean(), nullable=False, default=False, server_default=sa.sql.expression.false()
        ),
    )
    op.add_column('dataset', sa.Column('expirySetting', sa.String(), nullable=True))
    op.add_column('dataset', sa.Column('expiryMinDuration', sa.Integer(), nullable=True))
    op.add_column('dataset', sa.Column('expiryMaxDuration', sa.Integer(), nullable=True))
    op.add_column('share_object', sa.Column('expiryDate', sa.DateTime(), nullable=True))
    op.add_column('share_object', sa.Column('requestedExpiryDate', sa.DateTime(), nullable=True))
    op.add_column('share_object', sa.Column('lastExtensionDate', sa.DateTime(), nullable=True))
    op.add_column('share_object', sa.Column('extensionReason', sa.String(), nullable=True))
    op.add_column('share_object', sa.Column('submittedForExtension', sa.Boolean(), nullable=True))
    op.add_column('share_object', sa.Column('shareExpirationPeriod', sa.Integer(), nullable=True))
    op.add_column(
        'share_object',
        sa.Column(
            'nonExpirable', sa.Boolean(), nullable=False, default=False, server_default=sa.sql.expression.false()
        ),
    )
    print('Successfully added columns for share expiration')


def downgrade():
    print('Removing columns for share expiration')
    op.drop_column('dataset', 'enableExpiration')
    op.drop_column('dataset', 'expiryMinDuration')
    op.drop_column('dataset', 'expiryMaxDuration')
    op.drop_column('dataset', 'expirySetting')
    op.drop_column('share_object', 'expiryDate')
    op.drop_column('share_object', 'requestedExpiryDate')
    op.drop_column('share_object', 'lastExtensionDate')
    op.drop_column('share_object', 'extensionReason')
    op.drop_column('share_object', 'submittedForExtension')
    op.drop_column('share_object', 'nonExpirable')
    op.drop_column('share_object', 'shareExpirationPeriod')
    print('Successfully removed columns related to share expiration')
