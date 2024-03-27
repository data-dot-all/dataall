import logging

from dataall.core.permissions.db.tenant.tenant_models import Tenant

logger = logging.getLogger(__name__)


class TenantRepository:
    @staticmethod
    def find_tenant_by_name(session, tenant_name: str) -> Tenant:
        tenant = session.query(Tenant).filter(Tenant.name == tenant_name).first()
        return tenant
