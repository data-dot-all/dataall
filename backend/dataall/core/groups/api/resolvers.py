import os
import logging

from dataall.base.context import get_context
from dataall.core.groups.db.group_models import Group
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.groups.services.group_service import GroupService
from dataall.core.permissions.db.tenant_policy_repositories import TenantPolicy
from dataall.base.db import exceptions

log = logging.getLogger()


def resolve_group_environment_permissions(context, source, environmentUri):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return EnvironmentService.list_group_permissions(session=session, uri=environmentUri, group_uri=source.groupUri)


def resolve_group_tenant_permissions(context, source):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return TenantPolicy.list_group_tenant_permissions(
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


def list_groups(context, source, filter: dict = None):
    with context.engine.scoped_session() as session:
        return GroupService.list_groups_without_invited(session, filter)


def get_groups_for_user(context, source, userid):
    request_context = get_context()
    if request_context.user_id != userid:
        raise Exception("User Id doesn't match user id from context")

    return GroupService.get_groups_for_user(userid)
