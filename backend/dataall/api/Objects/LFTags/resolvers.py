

import os

from .... import db
from ....aws.handlers.sts import SessionHelper
from ....aws.handlers.parameter_store import ParameterStoreManager
from ....aws.handlers.quicksight import Quicksight
from ....db import exceptions


def list_tenant_lf_tags(context, source, filter=None):
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        admin = db.api.TenantPolicy.is_tenant_admin(context.groups)

        if not admin:
            raise db.exceptions.TenantUnauthorized(
                username=context.username,
                action=db.permissions.TENANT_ALL,
                tenant_name=context.username,
            )
        return db.api.LFTag.list_tenant_lf_tags(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=None,
            data=filter,
            check_perm=True,
        )


def remove_lf_tag(context, source, lftagUri):
    with context.engine.scoped_session() as session:
        admin = db.api.TenantPolicy.is_tenant_admin(context.groups)
        if not admin:
            raise db.exceptions.TenantUnauthorized(
                username=context.username,
                action=db.permissions.TENANT_ALL,
                tenant_name=context.username,
            )
        status = db.api.LFTag.remove_lf_tag(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=lftagUri,
            # check_perm=True,
        )

    return status


def add_lf_tag(context, source, input):
    with context.engine.scoped_session() as session:
        admin = db.api.TenantPolicy.is_tenant_admin(context.groups)

        if not admin:
            raise db.exceptions.TenantUnauthorized(
                username=context.username,
                action=db.permissions.TENANT_ALL,
                tenant_name=context.username,
            )
        tag = db.api.LFTag.add_lf_tag(
            session=session,
            username=context.username,
            groups=context.groups,
            data=input,
            # check_perm=True,
        )

    return tag


def list_all_lf_tags(
    context, source, environmentUri=None, filter=None
):
    if filter is None:
        filter = {}
    with context.engine.scoped_session() as session:
        return db.api.LFTag.list_all_lf_tags(session)
