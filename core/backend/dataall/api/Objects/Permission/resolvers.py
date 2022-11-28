import logging

from .... import db
from ....api.context import Context

log = logging.getLogger(__name__)


def list_tenant_permissions(
    context: Context,
    source,
    filter: dict = None,
):
    with context.engine.scoped_session() as session:
        if not filter:
            filter = {}
        return db.api.Permission.paginated_tenant_permissions(
            session=session, data=filter
        )


def list_resource_permissions(
    context: Context,
    source,
    filter: dict = None,
):
    with context.engine.scoped_session() as session:
        if not filter:
            filter = {}
        return db.api.Permission.paginated_resource_permissions(
            session=session, data=filter
        )
