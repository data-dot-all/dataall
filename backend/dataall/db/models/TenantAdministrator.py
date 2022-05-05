from sqlalchemy import Column, ForeignKey, String

from .. import Base
from .Tenant import Tenant


class TenantAdministrator(Base):
    __tablename__ = "tenant_administrator"
    userName = Column(String, primary_key=True, nullable=False)
    tenantUri = Column(String, ForeignKey(Tenant.tenantUri), nullable=False)
    userRoleInTenant = Column(String, nullable=False, default="ADMIN")
