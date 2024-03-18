import logging

from dataall.core.permissions.db.tenant import tenant_models as models

logger = logging.getLogger(__name__)


class Tenant:
    @staticmethod
    def find_tenant_by_name(session, tenant_name: str) -> models.Tenant:
        if tenant_name:
            tenant = session.query(models.Tenant).filter(models.Tenant.name == tenant_name).first()
            return tenant

    @staticmethod
    def get_tenant_by_name(session, tenant_name: str) -> models.Tenant:
        if not tenant_name:
            raise Exception('Tenant name is required')
        tenant = Tenant.find_tenant_by_name(session, tenant_name)
        if not tenant:
            raise Exception('TenantNotFound')
        return tenant

    @staticmethod
    def save_tenant(session, name: str, description: str) -> models.Tenant:
        if not name:
            raise Exception('Tenant name is required')

        tenant = Tenant.find_tenant_by_name(session, name)
        if tenant:
            return tenant
        else:
            tenant = models.Tenant(name=name, description=description if description else f'Tenant {name}')
            session.add(tenant)
            session.commit()
        return tenant
