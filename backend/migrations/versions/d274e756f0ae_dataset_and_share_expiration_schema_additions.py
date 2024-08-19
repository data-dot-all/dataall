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
down_revision = '9efe5f7c69a1'
branch_labels = None
depends_on = None


def upgrade():
    envname = os.getenv('envname', 'local')
    print('ENVNAME', envname)
    engine = get_engine(envname=envname).engine

    # Add Columns to the dataset base table
    op.add_column(
        'dataset',
        sa.Column(
            'enableExpiration', sa.Boolean(), nullable=False, default=False, server_default=sa.sql.expression.false()
        ),
    ) if not has_column(schema=envname, table='dataset', column='enableExpiration', engine=engine) else print(
        'Column enableExpiration already exists in dataset table'
    )
    op.add_column('dataset', sa.Column('expirySetting', sa.String(), nullable=True)) if not has_column(
        schema=envname, table='dataset', column='expirySetting', engine=engine
    ) else print('Column expirySetting already exists in dataset table')
    op.add_column('dataset', sa.Column('expiryMinDuration', sa.Integer(), nullable=True)) if not has_column(
        schema=envname, table='dataset', column='expiryMinDuration', engine=engine
    ) else print('Column expiryMinDuration already exists in dataset table')
    op.add_column('dataset', sa.Column('expiryMaxDuration', sa.Integer(), nullable=True)) if not has_column(
        schema=envname, table='dataset', column='expiryMaxDuration', engine=engine
    ) else print('Column expiryMaxDuration already exists in dataset table')

    op.add_column('share_object', sa.Column('expiryDate', sa.DateTime(), nullable=True)) if not has_column(
        schema=envname, table='share_object', column='expiryDate', engine=engine
    ) else print('Column expiryDate already exists in share_object table')
    op.add_column('share_object', sa.Column('requestedExpiryDate', sa.DateTime(), nullable=True)) if not has_column(
        schema=envname, table='share_object', column='requestedExpiryDate', engine=engine
    ) else print('Column requestedExpiryDate already exists in share_object table')
    op.add_column('share_object', sa.Column('lastExtensionDate', sa.DateTime(), nullable=True)) if not has_column(
        schema=envname, table='share_object', column='lastExtensionDate', engine=engine
    ) else print('Column lastExtensionDate already exists in share_object table')
    op.add_column('share_object', sa.Column('extensionReason', sa.String(), nullable=True)) if not has_column(
        schema=envname, table='share_object', column='extensionReason', engine=engine
    ) else print('Column extensionReason already exists in share_object table')
    op.add_column('share_object', sa.Column('submittedForExtension', sa.Boolean(), nullable=True)) if not has_column(
        schema=envname, table='share_object', column='submittedForExtension', engine=engine
    ) else print('Column submittedForExtension already exists in share_object table')


def downgrade():
    envname = os.getenv('envname', 'local')
    print('ENVNAME', envname)
    engine = get_engine(envname=envname).engine

    op.drop_column('dataset', 'enableExpiration') if has_column(
        schema=envname, table='dataset', column='enableExpiration', engine=engine
    ) else print('Column enableExpiration does not exists in dataset table')
    op.drop_column('dataset', 'expiryMinDuration') if has_column(
        schema=envname, table='dataset', column='expiryMinDuration', engine=engine
    ) else print('Column expiryMinDuration does not exists in dataset table')
    op.drop_column('dataset', 'expiryMaxDuration') if has_column(
        schema=envname, table='dataset', column='expiryMaxDuration', engine=engine
    ) else print('Column expiryMaxDuration does not exists in dataset table')
    op.drop_column('dataset', 'expirySetting') if has_column(
        schema=envname, table='dataset', column='expirySetting', engine=engine
    ) else print('Column expirySetting does not exists in dataset table')
    op.drop_column('share_object', 'expiryDate') if has_column(
        schema=envname, table='share_object', column='expiryDate', engine=engine
    ) else print('Column expiryDate does not exists in share_object table')
    op.drop_column('share_object', 'requestedExpiryDate') if has_column(
        schema=envname, table='share_object', column='requestedExpiryDate', engine=engine
    ) else print('Column requestedExpiryDate does not exists in share_object table')
    op.drop_column('share_object', 'lastExtensionDate') if has_column(
        schema=envname, table='share_object', column='lastExtensionDate', engine=engine
    ) else print('Column lastExtensionDate does not exists in share_object table')
    op.drop_column('share_object', 'extensionReason') if has_column(
        schema=envname, table='share_object', column='extensionReason', engine=engine
    ) else print('Column extensionReason does not exists in share_object table')
    op.drop_column('share_object', 'submittedForExtension') if has_column(
        schema=envname, table='share_object', column='submittedForExtension', engine=engine
    ) else print('Column submittedForExtension does not exists in share_object table')
