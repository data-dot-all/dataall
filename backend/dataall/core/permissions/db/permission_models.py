import datetime
import enum

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as DBEnum
from sqlalchemy.orm import relationship

from dataall.base.db import Base, utils


class PermissionType(enum.Enum):
    TENANT = 'TENANT'
    RESOURCE = 'RESOURCE'


class Permission(Base):
    __tablename__ = 'permission'
    permissionUri = Column(String, primary_key=True, default=utils.uuid('permission'))
    name = Column(String, nullable=False, index=True)
    type = Column(DBEnum(PermissionType), nullable=False)
    description = Column(String, nullable=False)
    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)


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


class TenantPolicyPermission(Base):
    __tablename__ = 'tenant_policy_permission'

    sid = Column(String, ForeignKey(TenantPolicy.sid), primary_key=True)
    permissionUri = Column(
        String, ForeignKey(Permission.permissionUri), primary_key=True
    )
    permission = relationship('Permission')
    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)


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


class ResourcePolicyPermission(Base):
    __tablename__ = 'resource_policy_permission'

    sid = Column(String, ForeignKey(ResourcePolicy.sid), primary_key=True)
    permissionUri = Column(
        String, ForeignKey(Permission.permissionUri), primary_key=True
    )
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
