import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from .. import Base
from . import Permission, ResourcePolicy


class ResourcePolicyPermission(Base):
    __tablename__ = 'resource_policy_permission'

    sid = Column(String, ForeignKey(ResourcePolicy.sid), primary_key=True)
    permissionUri = Column(
        String, ForeignKey(Permission.permissionUri), primary_key=True
    )
    permission = relationship('Permission')
    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)
