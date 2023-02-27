"""
Contains decorators that check if user has a permission to access
and interact with resources or do some actions in the app
"""
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


def has_resource_permission(permission):
    """
    Decorator that check if a user has access to the resource.
    The method or function decorated with this decorator must have a URI of accessing resource
    Good rule of thumb: if there is a URI that accesses a specific resource,
    hence it has URI - it must be decorated with this decorator
    """
    def decorator(f):
        static_func = False
        try:
            f.__func__
            static_func = True
            fn = f.__func__
        except AttributeError:
            fn = f

        def decorated(*args, uri, **kwargs):
            context: RequestContext = get_context()
            db = context.db_engine
            # trying to re-use the open session if there is one
            if not db.current_session():
                _check_resource_permission(db.current_session(), uri, permission)
            else:
                with db.scoped_session() as session:
                    _check_resource_permission(session, uri, permission)
            return fn(*args, uri=uri, **kwargs)

        if static_func:
            return staticmethod(decorated)
        else:
            return decorated

    return decorator


def has_tenant_permission(permission: str):
    """
    Decorator to check if a user has a permission to do some action.
    All the information about the user is retrieved from RequestContext
    """
    def decorator(f):
        static_func = False
        try:
            f.__func__
            static_func = True
            fn = f.__func__
        except AttributeError:
            fn = f

        def decorated(*args, **kwargs):
            context: RequestContext = get_context()
            db = context.db_engine
            # trying to re-use the open session if there is one
            if not db.current_session():
                _check_tenant_permission(db.current_session(), permission)
            else:
                with db.scoped_session() as session:
                    _check_tenant_permission(session, permission)

            return fn(*args, **kwargs)

        if static_func:
            return staticmethod(decorated)
        else:
            return decorated

    return decorator


def has_group_permission(permission):
    def decorator(f):
        static_func = False
        try:
            f.__func__
            static_func = True
            fn = f.__func__
        except AttributeError:
            fn = f

        def decorated(*args, admin_group, uri, **kwargs):
            context: RequestContext = get_context()
            db = context.db_engine

            # trying to re-use the open session if there is one
            if not db.current_session():
                _check_group_environment_permission(db.current_session(), permission, uri, admin_group)
            else:
                with db.scoped_session() as session:
                    _check_group_environment_permission(session, permission, uri, admin_group)
            return fn(*args, uri=uri, admin_group=admin_group, **kwargs)

        if static_func:
            return staticmethod(decorated)
        else:
            return decorated

    return decorator
