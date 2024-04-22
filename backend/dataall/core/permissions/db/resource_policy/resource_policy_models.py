import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as DBEnum
from sqlalchemy.orm import relationship

from dataall.base.db import Base, utils

from dataall.core.permissions.db.permission.permission_models import Permission


class ResourcePolicy(Base):
    __tablename__ = 'resource_policy'

    sid = Column(String, primary_key=True, default=utils.uuid('resource_policy'))

    resourceUri = Column(String, nullable=False, index=True)
    resourceType = Column(String, nullable=False, index=True)

    principalId = Column(String, nullable=False, index=True)
    principalType = Column(DBEnum('USER', 'GROUP', 'SERVICE', name='rp_principal_type'), default='GROUP')

    permissions = relationship('ResourcePolicyPermission', uselist=True, backref='resource_policy')

    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)


class ResourcePolicyPermission(Base):
    __tablename__ = 'resource_policy_permission'

    sid = Column(String, ForeignKey(ResourcePolicy.sid), primary_key=True)
    permissionUri = Column(String, ForeignKey(Permission.permissionUri), primary_key=True)
    permission = relationship('Permission')
    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)
