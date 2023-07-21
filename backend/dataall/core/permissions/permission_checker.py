"""
Contains decorators that check if user has a permission to access
and interact with resources or do some actions in the app
"""
from typing import Protocol, Callable

from dataall.base.context import RequestContext, get_context
from dataall.core.permissions.db.resource_policy import ResourcePolicy
from dataall.core.permissions.db.tenant_policy import TenantPolicy
from dataall.base.utils.decorator_utls import process_func


class Identifiable(Protocol):
    """Protocol to identify resources for checking permissions"""
    def get_resource_uri(self) -> str:
        ...


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



def has_resource_permission(
        permission: str,
        param_name: str = None,
        resource_name: str = None,
        parent_resource: Callable = None
):
    """
    Decorator that check if a user has access to the resource.
    The method or function decorated with this decorator must have a URI of accessing resource
    Good rule of thumb: if there is a URI that accesses a specific resource,
    hence it has URI - it must be decorated with this decorator
    """
    if not param_name:
        param_name = "uri"

    def decorator(f):
        fn, fn_decorator = process_func(f)

        def decorated(*args, **kwargs):
            uri: str
            if resource_name:
                resource: Identifiable = kwargs[resource_name]
                uri = resource.get_resource_uri()
            else:
                if param_name not in kwargs:
                    raise KeyError(f"{f.__name__} doesn't have parameter {param_name}")
                uri = kwargs[param_name]

            with get_context().db_engine.scoped_session() as session:
                if parent_resource:
                    try:
                        uri = parent_resource(session, uri)
                    except TypeError:
                        uri = parent_resource.__func__(session, uri)

                _check_resource_permission(session, uri, permission)

            return fn(*args, **kwargs)

        return fn_decorator(decorated)

    return decorator


def has_tenant_permission(permission: str):
    """
    Decorator to check if a user has a permission to do some action.
    All the information about the user is retrieved from RequestContext
    """
    def decorator(f):
        fn, fn_decorator = process_func(f)

        def decorated(*args, **kwargs):
            with get_context().db_engine.scoped_session() as session:
                _check_tenant_permission(session, permission)

            return fn(*args, **kwargs)

        return fn_decorator(decorated)

    return decorator
