import os
from .... import db
from ....db import exceptions
from ....db.models import Group
from ...constants import *
from ....aws.handlers.parameter_store import ParameterStoreManager
from ....aws.handlers.sts import SessionHelper
from ....aws.handlers.cognito import Cognito


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

def list_cognito_groups(context, source):
    current_account = SessionHelper.get_account()
    current_region = os.getenv('AWS_REGION', 'eu-west-1')
    envname = os.getenv('envname', 'local')
    if envname in ['local', 'dkrcompose']:
        return [{"groupName": 'DAAdministrators'}, {"groupName": 'Engineers'}, {"groupName": 'Scientists'}]
    parameter_path = f'/dataall/{envname}/cognito/userpool'
    user_pool_id = ParameterStoreManager.get_parameter_value(current_account, current_region, parameter_path)
    groups = Cognito.list_cognito_groups(current_account, current_region, user_pool_id)
    res = []
    for group in groups:
        res.append({"groupName": group['GroupName']})

    return res
