import logging

from dataall.core.permissions.db.permission import Permission

log = logging.getLogger(__name__)


def list_tenant_permissions(
    context,
    source,
    filter: dict = None,
):
    with context.engine.scoped_session() as session:
        if not filter:
            filter = {}
        return Permission.paginated_tenant_permissions(
            session=session, data=filter
        )
