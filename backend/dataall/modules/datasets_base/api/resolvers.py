import logging

from dataall.base.api.context import Context
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.organizations.db.organization_repositories import OrganizationRepository
from dataall.core.stacks.services.stack_service import StackService
from dataall.modules.datasets_base.services.dataset_list_service import DatasetListService
from dataall.modules.datasets_base.services.datasets_enums import DatasetRole
from dataall.modules.datasets_base.db.dataset_models import DatasetBase

log = logging.getLogger(__name__)


def list_all_user_datasets(context: Context, source, filter: dict = None):
    if not filter:
        filter = {'page': 1, 'pageSize': 5}
    return DatasetListService.list_all_user_datasets(filter)


def list_owned_datasets(context: Context, source, filter: dict = None):
    if not filter:
        filter = {'page': 1, 'pageSize': 5}
    return DatasetListService.list_owned_datasets(filter)


def list_datasets_created_in_environment(context: Context, source, environmentUri: str = None, filter: dict = None):
    if not filter:
        filter = {}
    return DatasetListService.list_datasets_created_in_environment(uri=environmentUri, data=filter)


def resolve_user_role(context: Context, source: DatasetBase, **kwargs):
    if not source:
        return None
    if source.owner == context.username:
        return DatasetRole.Creator.value
    elif source.SamlAdminGroupName in context.groups:
        return DatasetRole.Admin.value
    elif source.stewards in context.groups:
        return DatasetRole.DataSteward.value
    else:
        with context.engine.scoped_session() as session:
            other_modules_user_role = DatasetListService.get_other_modules_dataset_user_role(
                session, source.datasetUri, context.username, context.groups
            )
            if other_modules_user_role is not None:
                return other_modules_user_role
    return DatasetRole.NoPermission.value


def get_dataset_organization(context, source: DatasetBase, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return OrganizationRepository.get_organization_by_uri(session, source.organizationUri)


def get_dataset_environment(context, source: DatasetBase, **kwargs):
    if not source:
        return None
    return EnvironmentService.find_environment_by_uri(uri=source.environmentUri)


def get_dataset_owners_group(context, source: DatasetBase, **kwargs):
    if not source:
        return None
    return source.SamlAdminGroupName


def get_dataset_stewards_group(context, source: DatasetBase, **kwargs):
    if not source:
        return None
    return source.stewards


def resolve_dataset_stack(context: Context, source: DatasetBase, **kwargs):
    if not source:
        return None
    return StackService.resolve_parent_obj_stack(
        targetUri=source.datasetUri,
        targetType='dataset',
        environmentUri=source.environmentUri,
    )
