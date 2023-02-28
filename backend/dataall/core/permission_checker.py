"""
Contains decorators that check if user has a permission to access
and interact with resources or do some actions in the app
"""
import contextlib

from dataall.core.context import RequestContext, get_context
from dataall.db.api import TenantPolicy, ResourcePolicy, Environment


def _check_group_environment_permission(session, permission, uri, admin_group):
    context: RequestContext = get_context()
    Environment.check_group_environment_permission(
        session=session,
        username=context.username,
        groups=context.groups,
        uri=uri,
        group=admin_group,
        permission_name=permission,
    )


def _check_tenant_permission(session, permission):
    context: RequestContext = get_context()
    TenantPolicy.check_user_tenant_permission(
        session=session,
        username=context.username,
        groups=context.groups,
        tenant_name='dataall',
        permission_name=permission
    )


def _check_resource_permission(session, uri, permission):
    context: RequestContext = get_context()
    ResourcePolicy.check_user_resource_permission(
        session=session,
        username=context.username,
        groups=context.groups,
        resource_uri=uri,
        permission_name=permission,
    )

@contextlib.contextmanager
def _get_session():
    context: RequestContext = get_context()
    db = context.db_engine

    # trying to re-use the open session if there is one
    if db.current_session():
        yield db.current_session()
    else:
        yield db.scoped_session()


def _process_func(func):
    """Helper function that helps decorate methods/functions"""
    def no_decorated(f):
        return f

    static_func = False
    try:
        func.__func__
        static_func = True
        fn = func.__func__
    except AttributeError:
        fn = func

    # returns a function to call and static decorator if applied
    return fn, staticmethod if static_func else no_decorated


def has_resource_permission(permission):
    """
    Decorator that check if a user has access to the resource.
    The method or function decorated with this decorator must have a URI of accessing resource
    Good rule of thumb: if there is a URI that accesses a specific resource,
    hence it has URI - it must be decorated with this decorator
    """
    def decorator(f):
        fn, fn_decorator = _process_func(f)

        def decorated(*args, uri, **kwargs):
            with _get_session() as session:
                _check_resource_permission(session, uri, permission)

            return fn(*args, uri=uri, **kwargs)

        return fn_decorator(decorated)

    return decorator


def has_tenant_permission(permission: str):
    """
    Decorator to check if a user has a permission to do some action.
    All the information about the user is retrieved from RequestContext
    """
    def decorator(f):
        fn, fn_decorator = _process_func(f)

        def decorated(*args, **kwargs):
            context: RequestContext = get_context()
            db = context.db_engine
            with _get_session() as session:
                _check_tenant_permission(session, permission)

            return fn(*args, **kwargs)

        return fn_decorator(decorated)

    return decorator


def has_group_permission(permission):
    def decorator(f):
        fn, fn_decorator = _process_func(f)

        def decorated(*args, admin_group, uri, **kwargs):
            context: RequestContext = get_context()
            db = context.db_engine

            with _get_session() as session:
                _check_group_environment_permission(session, permission, uri, admin_group)

            return fn(*args, uri=uri, admin_group=admin_group, **kwargs)

        return fn_decorator(decorated)

    return decorator
