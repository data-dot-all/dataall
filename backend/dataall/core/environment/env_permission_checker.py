from dataall.base.context import get_context, RequestContext
from dataall.core.permissions.db.group_policy import GroupPolicy
from dataall.utils.decorator_utls import process_func


def _check_group_environment_permission(session, permission, uri, admin_group):
    context: RequestContext = get_context()
    GroupPolicy.check_group_environment_permission(
        session=session,
        username=context.username,
        groups=context.groups,
        uri=uri,
        group=admin_group,
        permission_name=permission,
    )


def has_group_permission(permission):
    def decorator(f):
        fn, fn_decorator = process_func(f)

        def decorated(*args, admin_group, uri, **kwargs):
            with get_context().db_engine.scoped_session() as session:
                _check_group_environment_permission(session, permission, uri, admin_group)

            return fn(*args, uri=uri, admin_group=admin_group, **kwargs)

        return fn_decorator(decorated)

    return decorator
