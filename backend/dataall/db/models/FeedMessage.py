from datetime import datetime

from sqlalchemy import Column, DateTime, String

from .. import Base, utils


class FeedMessage(Base):
    __tablename__ = 'feed_message'
    feedMessageUri = Column(String, primary_key=True, default=utils.uuid('_'))
    creator = Column(String, nullable=False)
    created = Column(DateTime, nullable=False, default=datetime.now)
    content = Column(String, nullable=True)
    targetUri = Column(String, nullable=False)
    targetType = Column(String, nullable=False)
