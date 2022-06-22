from .... import db
from ....db import exceptions
from ....db.models import Group
from ...constants import *


def resolve_group_environment_permissions(context, source, environmentUri):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return db.api.Environment.list_group_permissions(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=environmentUri,
            data={'groupUri': source.groupUri},
            check_perm=True,
        )


def resolve_group_tenant_permissions(context, source):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return db.api.TenantPolicy.list_group_tenant_permissions(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=source.groupUri,
            data=None,
            check_perm=True,
        )


def get_group(context, source, groupUri):
    if not groupUri:
        exceptions.RequiredParameter('groupUri')
    return Group(groupUri=groupUri, name=groupUri, label=groupUri)


def list_datasets_owned_by_env_group(
    context, source, environmentUri: str = None, groupUri: str = None, filter: dict = None
):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return db.api.Environment.paginated_environment_group_datasets(
            session=session,
            username=context.username,
            groups=context.groups,
            envUri=environmentUri,
            groupUri=groupUri,
            data=filter,
            check_perm=True,
        )


def list_data_items_shared_with_env_group(
    context, source, environmentUri: str = None, groupUri: str = None, filter: dict = None
):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return db.api.Environment.paginated_shared_with_environment_group_datasets(
            session=session,
            username=context.username,
            groups=context.groups,
            envUri=environmentUri,
            groupUri=groupUri,
            data=filter,
            check_perm=True,
        )
