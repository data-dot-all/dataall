"""sharing_state_machines_v1_4_0

Revision ID: 2035e87072dd
Revises: 04d92886fabe
Create Date: 2023-01-04 11:36:15.021780

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm, Column, String, Boolean, DateTime, and_
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base

from dataall.db import api, models, permissions, utils
from dataall.db.models.Enums import ShareObjectStatus, ShareItemStatus
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '2035e87072dd'
down_revision = '509997f0a51e'
branch_labels = None
depends_on = None

Base = declarative_base()


class ShareObject(Base):
    __tablename__ = 'share_object'
    shareUri = Column(
        String, nullable=False, primary_key=True, default=utils.uuid('share')
    )
    datasetUri = Column(String, nullable=False)
    environmentUri = Column(String)
    groupUri = Column(String)
    principalIAMRoleName = Column(String, nullable=True)
    principalId = Column(String, nullable=True)
    principalType = Column(String, nullable=True, default='Group')
    status = Column(String, nullable=False, default=ShareObjectStatus.Draft.value)
    owner = Column(String, nullable=False)
    created = Column(DateTime, default=datetime.now)
    updated = Column(DateTime, onupdate=datetime.now)
    deleted = Column(DateTime)
    confirmed = Column(Boolean, default=False)


class ShareObjectItem(Base):
    __tablename__ = 'share_object_item'
    shareUri = Column(String, nullable=False)
    shareItemUri = Column(
        String, default=utils.uuid('shareitem'), nullable=False, primary_key=True
    )
    itemType = Column(String, nullable=False)
    itemUri = Column(String, nullable=False)
    itemName = Column(String, nullable=False)
    permission = Column(String, nullable=True)
    created = Column(DateTime, nullable=False, default=datetime.now)
    updated = Column(DateTime, nullable=True, onupdate=datetime.now)
    deleted = Column(DateTime, nullable=True)
    owner = Column(String, nullable=False)
    GlueDatabaseName = Column(String, nullable=True)
    GlueTableName = Column(String, nullable=True)
    S3AccessPointName = Column(String, nullable=True)
    status = Column(String, nullable=False, default=ShareItemStatus.PendingApproval.value)
    action = Column(String, nullable=True)


def upgrade():
    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)
        print('Updating share Objects...')
        (
            session.query(ShareObject)
            .filter(
                ShareObject.status == 'PendingApproval'
            )
            .update(
                {
                    ShareObject.status == 'Completed'
                }
            )
        )

        print('Share Objects updated successfully')
        print('Updating share Items..')
        (
            session.query(ShareObject)
            .filter(
                ShareObject.status == 'Draft'
            )
            .update(
                {
                    ShareObject.status == 'PendingApproval'
                }
            )
        )

        print('Share Items updated successfully')
    except Exception as e:
        print(f'Failed to backfill share_objects due to: {e}')
    # ### end Alembic commands ###


def downgrade():
    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)
        print('Updating share Objects...')
        (
            session.query(ShareObject)
            .filter(
                ShareObject.status == 'Completed'
            )
            .update(
                {
                    ShareObject.status == 'PendingApproval'
                }
            )
        )

        print('Share Objects updated successfully')
        print('Updating share Items..')
        (
            session.query(ShareObject)
            .filter(
                ShareObject.status == 'PendingApproval'
            )
            .update(
                {
                    ShareObject.status == 'Draft'
                }
            )
        )

        print('Share Items updated successfully')
    except Exception as e:
        print(f'Failed to backfill share_objects due to: {e}')
    # ### end Alembic commands ###
