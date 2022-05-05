from datetime import datetime

from sqlalchemy import Column, DateTime, String

from .. import Base, utils
from .Enums import ShareObjectStatus


class ShareObjectItem(Base):
    __tablename__ = "share_object_item"
    shareUri = Column(String, nullable=False)
    shareItemUri = Column(String, default=utils.uuid("shareitem"), nullable=False, primary_key=True)
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
    status = Column(String, nullable=False, default=ShareObjectStatus.Draft.value)
    action = Column(String, nullable=True)
