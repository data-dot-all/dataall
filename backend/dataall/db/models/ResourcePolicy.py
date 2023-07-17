import datetime

from sqlalchemy import Column, String, DateTime, Enum as DBEnum
from sqlalchemy.orm import relationship

from .. import Base, utils


class ResourcePolicy(Base):
    __tablename__ = 'resource_policy'

    sid = Column(String, primary_key=True, default=utils.uuid('resource_policy'))

    resourceUri = Column(String, nullable=False, index=True)
    resourceType = Column(String, nullable=False, index=True)

    principalId = Column(String, nullable=False, index=True)
    principalType = Column(
        DBEnum('USER', 'GROUP', 'SERVICE', name='rp_principal_type'), default='GROUP'
    )

    permissions = relationship(
        'ResourcePolicyPermission', uselist=True, backref='resource_policy'
    )

    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)
