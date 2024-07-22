"""describe_changes_shortly

Revision ID: d274e756f0ae
Revises: 797dd1012be1
Create Date: 2024-07-18 14:25:20.728900

"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, String, ForeignKey, ARRAY, Boolean, Enum, orm, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import query_expression

from dataall.base.db import Resource, utils
from dataall.core.environment.api.enums import EnvironmentType
from dataall.modules.datasets_base.services.datasets_enums import Language, ConfidentialityClassification, DatasetTypes
from dataall.modules.shares_base.services.shares_enums import ShareObjectStatus

# revision identifiers, used by Alembic.
revision = 'd274e756f0ae'
down_revision = '797dd1012be1'
branch_labels = None
depends_on = None


def upgrade():
    # Add Columns to the dataset base table
    op.add_column('dataset', sa.Column('enableExpiration', sa.Boolean(), nullable=False, default=False, server_default=sa.sql.expression.false()))
    op.add_column('dataset', sa.Column('expirySetting', sa.String(), nullable=True))
    op.add_column('dataset', sa.Column('expiryMinDuration', sa.Integer(), nullable=True))
    op.add_column('dataset', sa.Column('expiryMaxDuration', sa.Integer(), nullable=True))

    op.add_column('share_object', sa.Column('expiryDate', sa.DateTime(), nullable=True))
    op.add_column('share_object', sa.Column('lastExtensionDate', sa.DateTime(), nullable=True))
    op.add_column('share_object', sa.Column('extensionReason', sa.String(), nullable=True))
    op.add_column('share_object', sa.Column('submittedForExtension', sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column('dataset', 'enableExpiration')
    op.drop_column('dataset', 'expiryMinDuration')
    op.drop_column('dataset', 'expiryMaxDuration')
    op.drop_column('share_object', 'expiryDate')
    op.drop_column('share_object', 'lastExtensionDate')
    op.drop_column('share_object', 'extensionReason')
    op.drop_column('share_object', 'submittedForExtension')
