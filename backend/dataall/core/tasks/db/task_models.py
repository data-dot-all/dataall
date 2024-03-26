import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects import postgresql

from dataall.base.db import Base
from dataall.base.db import utils


class Task(Base):
    __tablename__ = 'task'
    taskUri = Column(String, nullable=False, default=utils.uuid('Task'), primary_key=True)
    targetUri = Column(String, nullable=False)
    cronexpr = Column(String, nullable=True)
    status = Column(String, nullable=False, default='pending')
    action = Column(String, nullable=False)
    payload = Column(postgresql.JSON, nullable=True)
    created = Column(DateTime, default=datetime.datetime.now())
    updated = Column(DateTime, onupdate=datetime.datetime.now())
    response = Column(postgresql.JSON)
    error = Column(postgresql.JSON)
    lastSeen = Column(DateTime, default=lambda: datetime.datetime(year=1900, month=1, day=1))
