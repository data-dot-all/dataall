import datetime
import enum

from sqlalchemy import Column, DateTime, Enum, String

from .. import Base, utils


class PermissionType(enum.Enum):
    TENANT = "TENANT"
    RESOURCE = "RESOURCE"


class Permission(Base):
    __tablename__ = "permission"
    permissionUri = Column(String, primary_key=True, default=utils.uuid("permission"))
    name = Column(String, nullable=False, index=True)
    type = Column(Enum(PermissionType), nullable=False)
    description = Column(String, nullable=False)
    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)
