import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from ... import Base
from . import ResourcePolicy
from . import Permission


class ResourcePolicyPermission(Base):
    __tablename__ = 'resource_policy_permission'

    sid = Column(String, ForeignKey(ResourcePolicy.sid), primary_key=True)
    permissionUri = Column(
        String, ForeignKey(Permission.permissionUri), primary_key=True
    )
    permission = relationship('Permission')
    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)
