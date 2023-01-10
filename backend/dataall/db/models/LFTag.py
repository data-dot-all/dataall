from sqlalchemy import Column, String, DateTime, ARRAY

from .. import Base
from .. import Resource, utils
import datetime
from sqlalchemy.dialects import postgresql


class LFTag(Base):
    __tablename__ = 'lftag'
    lftagUri = Column(String, primary_key=True, default=utils.uuid('lftag'))
    LFTagKey = Column(String, nullable=False)
    LFTagValues = Column(ARRAY(String))
    teams = Column(String, nullable=True)
    description = Column(String, nullable=True)
    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)
    deleted = Column(DateTime)
