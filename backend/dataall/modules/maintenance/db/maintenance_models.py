"""ORM models for maintenance activity"""

from sqlalchemy import Column, String

from dataall.base.db import Base


class Maintenance(Base):
    """ORM Model for maintenance window"""

    __tablename__ = 'maintenance'
    status = Column(String, nullable=False, primary_key=True)
    mode = Column(String, default='', nullable=True)
