import enum
from datetime import datetime

from sqlalchemy import Column, String, Boolean, Enum, DateTime

from dataall.db import Base
from dataall.db import utils


class NotificationType(enum.Enum):
    SHARE_OBJECT_SUBMITTED = 'SHARE_OBJECT_SUBMITTED'
    SHARE_ITEM_REQUEST = 'SHARE_ITEM_REQUEST'
    SHARE_OBJECT_APPROVED = 'SHARE_OBJECT_APPROVED'
    SHARE_OBJECT_REJECTED = 'SHARE_OBJECT_REJECTED'
    SHARE_OBJECT_PENDING_APPROVAL = 'SHARE_OBJECT_PENDING_APPROVAL'
    DATASET_VERSION = 'DATASET_VERSION'


class Notification(Base):
    __tablename__ = 'notification'
    notificationUri = Column(
        String, primary_key=True, default=utils.uuid('notificationtype')
    )
    type = Column(Enum(NotificationType), nullable=True)
    message = Column(String, nullable=False)
    username = Column(String, nullable=False)
    is_read = Column(Boolean, nullable=False, default=False)
    target_uri = Column(String)
    created = Column(DateTime, default=datetime.now)
    updated = Column(DateTime, onupdate=datetime.now)
    deleted = Column(DateTime)
