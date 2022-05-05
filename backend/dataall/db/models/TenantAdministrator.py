from sqlalchemy import Column, String, ForeignKey

from .Tenant import Tenant
from .. import Base


class TenantAdministrator(Base):
    __tablename__ = "tenant_administrator"
    userName = Column(String, primary_key=True, nullable=False)
    tenantUri = Column(String, ForeignKey(Tenant.tenantUri), nullable=False)
    userRoleInTenant = Column(String, nullable=False, default="ADMIN")
