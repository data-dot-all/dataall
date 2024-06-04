import logging
from dataall.base.context import get_context
from dataall.core.permissions.services.resource_policy_service import ResourcePolicyService
from dataall.modules.connections_base.db.connection_repositories import ConnectionRepository
from dataall.modules.connections_base.services.connection_list_permissions import LIST_ENVIRONMENT_CONNECTIONS


log = logging.getLogger(__name__)


class ConnectionListService:
    @staticmethod
    @ResourcePolicyService.has_resource_permission(LIST_ENVIRONMENT_CONNECTIONS)
    def list_environment_connections(uri, filter):
        context = get_context()
        with context.db_engine.scoped_session() as session:
            connections = ConnectionRepository.paginated_user_connections(
                session, context.username, context.groups, filter
            )
            return connections
