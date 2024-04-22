from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime

from dataall.base.db import Base
from dataall.base.db import utils


class Notification(Base):
    __tablename__ = 'notification'
    notificationUri = Column(String, primary_key=True, default=utils.uuid('notificationtype'))
    type = Column(String, nullable=True)
    message = Column(String, nullable=False)
    recipient = Column(String, nullable=False)  # recipients can be groups or individual users
    is_read = Column(Boolean, nullable=False, default=False)
    target_uri = Column(String)
    created = Column(DateTime, default=datetime.now)
    updated = Column(DateTime, onupdate=datetime.now)
    deleted = Column(DateTime)
