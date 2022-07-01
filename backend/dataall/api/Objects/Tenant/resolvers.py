from .... import db


def update_group_permissions(context, source, input=None):
    with context.engine.scoped_session() as session:
        return db.api.TenantPolicy.update_group_permissions(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=input['groupUri'],
            data=input,
            check_perm=True,
        )


def list_tenant_permissions(context, source):
    with context.engine.scoped_session() as session:
        return db.api.TenantPolicy.list_tenant_permissions(
            session=session, username=context.username, groups=context.groups
        )


def list_tenant_groups(context, source, filter=None):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return db.api.TenantPolicy.list_tenant_groups(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=None,
            data=filter,
            check_perm=True,
        )