import datetime

from sqlalchemy import Column, String, DateTime

from common.db import Base, utils


class Tenant(Base):
    __tablename__ = 'tenant'
    tenantUri = Column(String, primary_key=True, default=utils.uuid('tenant'))
    name = Column(String, nullable=False, index=True, unique=True)
    description = Column(String, default='No description provided')
    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)
