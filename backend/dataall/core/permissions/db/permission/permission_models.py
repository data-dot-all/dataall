import datetime

from dataall.core.permissions.api.enums import PermissionType
from sqlalchemy import Column, String, DateTime, Enum as DBEnum

from dataall.base.db import Base, utils


class Permission(Base):
    __tablename__ = 'permission'
    permissionUri = Column(String, primary_key=True, default=utils.uuid('permission'))
    name = Column(String, nullable=False, index=True)
    type = Column(DBEnum(PermissionType), nullable=False)
    description = Column(String, nullable=False)
    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)
