

import os

from .... import db
from ....aws.handlers.sts import SessionHelper
from ....aws.handlers.parameter_store import ParameterStoreManager
from ....aws.handlers.quicksight import Quicksight
from ....db import exceptions


def list_tenant_lf_tag_permissions(context, source, filter=None):
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
        return db.api.LFTagPermissions.list_tenant_lf_tag_permissions(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=None,
            data=filter,
            check_perm=True,
        )
