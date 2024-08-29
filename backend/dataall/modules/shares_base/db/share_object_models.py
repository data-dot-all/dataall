from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import Boolean, Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import query_expression

from dataall.base.db import Base, utils
from dataall.modules.shares_base.services.shares_enums import (
    ShareObjectStatus,
    ShareItemStatus,
)


def in_one_month():
    return datetime.now() + timedelta(days=31)


def _uuid4():
    return str(uuid4())


class ShareObject(Base):
    __tablename__ = 'share_object'
    shareUri = Column(String, nullable=False, primary_key=True, default=utils.uuid('share'))
    datasetUri = Column(String, nullable=False)
    environmentUri = Column(String)
    groupUri = Column(String)
    principalRoleName = Column(String, nullable=True)
    principalId = Column(String, nullable=True)
    principalType = Column(String, nullable=True, default='Group')
    status = Column(String, nullable=False, default=ShareObjectStatus.Draft.value)
    owner = Column(String, nullable=False)
    created = Column(DateTime, default=datetime.now)
    updated = Column(DateTime, onupdate=datetime.now)
    deleted = Column(DateTime)
    confirmed = Column(Boolean, default=False)
    requestPurpose = Column(String, nullable=True)
    rejectPurpose = Column(String, nullable=True)
    userRoleForShareObject = query_expression()
    existingSharedItems = query_expression()


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
    status = Column(String, nullable=False, default=ShareItemStatus.PendingApproval.value)
    action = Column(String, nullable=True)
    healthStatus = Column(String, nullable=True)
    healthMessage = Column(String, nullable=True)
    lastVerificationTime = Column(DateTime, nullable=True)
    attachedDataFilterUri = Column(
        String, ForeignKey('share_object_item_data_filter.attachedDataFilterUri'), nullable=True
    )


class ShareObjectItemDataFilter(Base):
    __tablename__ = 'share_object_item_data_filter'
    attachedDataFilterUri = Column(String, primary_key=True, default=utils.uuid('shareitemdatafilter'))
    label = Column(String, nullable=False)
    dataFilterUris = Column(ARRAY(String), nullable=False)
    dataFilterNames = Column(ARRAY(String), nullable=False)
    itemUri = Column(String, nullable=False)

    __table_args__ = (Index('ix_itemUri_label', 'itemUri', 'label', unique=True),)
