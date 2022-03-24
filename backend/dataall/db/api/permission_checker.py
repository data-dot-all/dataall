from ..api.resource_policy import ResourcePolicy
from ..api.tenant_policy import TenantPolicy


def has_resource_perm(permission):
    def decorator(f):
        static_func = False
        try:
            f.__func__
            static_func = True
            fn = f.__func__
        except AttributeError:
            fn = f

        def decorated(
            session,
            username: str,
            groups: [str],
            uri: str,
            data: dict = None,
            check_perm: bool = True,
        ):
            if check_perm:
                ResourcePolicy.check_user_resource_permission(
                    session=session,
                    username=username,
                    groups=groups,
                    resource_uri=uri,
                    permission_name=permission,
                )
            return fn(session, username, groups, uri, data=data, check_perm=check_perm)

        if static_func:
            return staticmethod(decorated)
        else:
            return decorated

    return decorator


def has_tenant_perm(permission):
    def decorator(f):
        static_func = False
        try:
            f.__func__
            static_func = True
            fn = f.__func__
        except AttributeError:
            fn = f

        def decorated(
            session,
            username: str,
            groups: [str],
            uri: str = None,
            data: dict = None,
            check_perm: bool = True,
        ):
            if check_perm:
                TenantPolicy.check_user_tenant_permission(
                    session=session,
                    username=username,
                    groups=groups,
                    tenant_name='dataall',
                    permission_name=permission,
                )
            return fn(
                session, username, groups, uri=uri, data=data, check_perm=check_perm
            )

        if static_func:
            return staticmethod(decorated)
        else:
            return decorated

    return decorator
