import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as DBEnum
from sqlalchemy.orm import relationship

from .. import Base, utils


class TenantPolicy(Base):
    __tablename__ = 'tenant_policy'

    sid = Column(String, primary_key=True, default=utils.uuid('tenant_policy'))

    tenantUri = Column(String, ForeignKey('tenant.tenantUri'), nullable=False)
    tenant = relationship('Tenant')

    principalId = Column(String, nullable=False, index=True)
    principalType = Column(
        DBEnum('USER', 'GROUP', 'SERVICE', name='tenant_principal_type'),
        default='GROUP',
    )

    permissions = relationship(
        'TenantPolicyPermission', uselist=True, backref='tenant_policy'
    )

    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)
