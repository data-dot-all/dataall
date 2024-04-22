import datetime

from sqlalchemy import Column, DateTime, String, Boolean
from sqlalchemy.dialects import postgresql

from dataall.base.db import Base
from dataall.base.db import utils


class Stack(Base):
    __tablename__ = 'stack'
    stackUri = Column(String, nullable=False, default=utils.uuid('stack'), primary_key=True)
    name = Column(String, nullable=True)
    targetUri = Column(String, nullable=False)
    accountid = Column(String, nullable=False)
    region = Column(String, nullable=False)
    cronexpr = Column(String, nullable=True)
    status = Column(String, nullable=False, default='pending')
    stack = Column(String, nullable=False)
    payload = Column(postgresql.JSON, nullable=True)
    created = Column(DateTime, default=datetime.datetime.now())
    updated = Column(DateTime, onupdate=datetime.datetime.now())
    stackid = Column(String)
    outputs = Column(postgresql.JSON)
    resources = Column(postgresql.JSON)
    error = Column(postgresql.JSON)
    events = Column(postgresql.JSON)
    lastSeen = Column(DateTime, default=lambda: datetime.datetime(year=1900, month=1, day=1))
    EcsTaskArn = Column(String, nullable=True)


class KeyValueTag(Base):
    __tablename__ = 'keyvaluetag'
    tagUri = Column(String, primary_key=True, default=utils.uuid('keyvaluetag'))
    targetUri = Column(String, nullable=False)
    targetType = Column(String, nullable=False)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)
    cascade = Column(Boolean, default=False)
