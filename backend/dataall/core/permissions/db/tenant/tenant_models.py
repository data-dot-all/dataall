import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as DBEnum
from sqlalchemy.orm import relationship

from dataall.base.db import Base, utils

from dataall.core.permissions.db.permission.permission_models import Permission


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

    permissions = relationship('TenantPolicyPermission', uselist=True, backref='tenant_policy')

    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)


class TenantPolicyPermission(Base):
    __tablename__ = 'tenant_policy_permission'

    sid = Column(String, ForeignKey(TenantPolicy.sid), primary_key=True)
    permissionUri = Column(String, ForeignKey(Permission.permissionUri), primary_key=True)
    permission = relationship('Permission')
    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)


class Tenant(Base):
    __tablename__ = 'tenant'
    tenantUri = Column(String, primary_key=True, default=utils.uuid('tenant'))
    name = Column(String, nullable=False, index=True, unique=True)
    description = Column(String, default='No description provided')
    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)
