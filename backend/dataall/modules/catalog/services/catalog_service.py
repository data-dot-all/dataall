import logging

from dataall.base.context import get_context
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyService

from dataall.modules.catalog.db.glossary_repositories import GlossaryRepository
from dataall.modules.catalog.db.glossary_models import GlossaryNode
from dataall.modules.catalog.services.glossaries_permissions import MANAGE_GLOSSARIES
from dataall.modules.catalog.indexers.registry import GlossaryRegistry
from dataall.core.permissions.services.tenant_policy_service import TenantPolicyValidationService
from dataall.core.tasks.db.task_models import Task
from dataall.core.tasks.service_handlers import Worker


logger = logging.getLogger(__name__)


def _session():
    return get_context().db_engine.scoped_session()


class CatalogService:
    @staticmethod
    def start_reindex_catalog(with_deletes: bool) -> bool:
        context = get_context()
        groups = context.groups if context.groups is not None else []
        if not TenantPolicyValidationService.is_tenant_admin(groups):
            raise Exception('Only data.all admin group members can start re-index catalog task')

        with context.db_engine.scoped_session() as session:
            reindex_catalog_task: Task = Task(
                action='ecs.reindex.catalog', targetUri='ALL', payload={'with_deletes': with_deletes}
            )
            session.add(reindex_catalog_task)

        Worker.queue(engine=context.db_engine, task_ids=[reindex_catalog_task.taskUri])
        return True
