"""sharing_state_machines_v1_4_0

Revision ID: 509997f0a51e
Revises: 04d92886fabe
Create Date: 2023-01-04 10:28:17.842210

"""

from alembic import op
from sqlalchemy import orm, Column, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

from dataall.base.db import utils
from datetime import datetime

from dataall.modules.shares_base.services.shares_enums import ShareObjectStatus, ShareItemStatus

# revision identifiers, used by Alembic.
revision = '509997f0a51e'
down_revision = 'd05f9a5b215e'
branch_labels = None
depends_on = None

Base = declarative_base()


class ShareObject(Base):
    __tablename__ = 'share_object'
    shareUri = Column(String, nullable=False, primary_key=True, default=utils.uuid('share'))
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
    shareItemUri = Column(String, default=utils.uuid('shareitem'), nullable=False, primary_key=True)
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
        print('Updating share Objects in PendingApproval...')
        (
            session.query(ShareObject)
            .filter(ShareObject.status == 'PendingApproval')
            .update({ShareObject.status: 'Submitted'})
        )
        print('Updating share Objects in Approved...')
        (session.query(ShareObject).filter(ShareObject.status == 'Approved').update({ShareObject.status: 'Processed'}))

        print('Share Objects updated successfully')
        print('Updating share Items in Draft..')
        (
            session.query(ShareObjectItem)
            .filter(ShareObjectItem.status == 'Draft')
            .update({ShareObjectItem.status: 'PendingApproval'})
        )

        print('Share Items updated successfully')
    except Exception as e:
        print(f'Failed to backfill share_objects due to: {e}')
    # ### end Alembic commands ###


def downgrade():
    try:
        bind = op.get_bind()
        session = orm.Session(bind=bind)
        print('Updating share Objects in PendingApproval...')
        (
            session.query(ShareObject)
            .filter(ShareObject.status == 'Submitted')
            .update({ShareObject.status: 'PendingApproval'})
        )
        print('Updating share Objects in Approved...')
        (session.query(ShareObject).filter(ShareObject.status == 'Processed').update({ShareObject.status: 'Approved'}))

        print('Share Objects updated successfully')
        print('Updating share Items in Draft..')
        (
            session.query(ShareObjectItem)
            .filter(ShareObjectItem.status == 'PendingApproval')
            .update({ShareObjectItem.status: 'Draft'})
        )

        print('Share Items updated successfully')
    except Exception as e:
        print(f'Failed to backfill share_objects due to: {e}')
    # ### end Alembic commands ###
