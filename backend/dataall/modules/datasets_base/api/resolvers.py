import logging

from dataall.core.stacks.api import stack_helper
from dataall.base.api.context import Context
from dataall.modules.catalog.db.glossary_repositories import GlossaryRepository
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.organizations.db.organization_repositories import OrganizationRepository
from dataall.modules.datasets_base.db.dataset_base_models import Dataset
from dataall.modules.datasets_base.services.datasets_base_enums import DatasetRole
from dataall.modules.datasets_base.services.dataset_base_service import DatasetListService

log = logging.getLogger(__name__)



#TODO: define in data_sharing_base to avoid circular dependencies
# def list_owned_shared_datasets(context: Context, source, filter: dict = None):
#     if not filter:
#         filter = {'page': 1, 'pageSize': 5}
#     return DatasetListService.list_owned_shared_datasets(filter)


def list_owned_datasets(context: Context, source, filter: dict = None):
    if not filter:
        filter = {'page': 1, 'pageSize': 5}
    return DatasetListService.list_owned_datasets(filter)

def get_dataset_organization(context, source: Dataset, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return OrganizationRepository.get_organization_by_uri(session, source.organizationUri)


def get_dataset_environment(context, source: Dataset, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return EnvironmentService.get_environment_by_uri(session, source.environmentUri)


def get_dataset_owners_group(context, source: Dataset, **kwargs):
    if not source:
        return None
    return source.SamlAdminGroupName


def get_dataset_stewards_group(context, source: Dataset, **kwargs):
    if not source:
        return None
    return source.stewards

def get_dataset_stack(context: Context, source: Dataset, **kwargs):
    if not source:
        return None
    return stack_helper.get_stack_with_cfn_resources(
        targetUri=source.datasetUri,
        environmentUri=source.environmentUri,
    )

def get_dataset_glossary_terms(context: Context, source: Dataset, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return GlossaryRepository.get_glossary_terms_links(session, source.datasetUri, 'Dataset')


def list_datasets_created_in_environment(context: Context, source, environmentUri: str = None, filter: dict = None):
    if not filter:
        filter = {}
    return DatasetListService.list_datasets_created_in_environment(uri=environmentUri, data=filter)


def list_datasets_owned_by_env_group(
    context, source, environmentUri: str = None, groupUri: str = None, filter: dict = None
):
    if not filter:
        filter = {}
    return DatasetListService.list_datasets_owned_by_env_group(environmentUri, groupUri, filter)

