import logging

from dataall.base.api.context import Context
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.organizations.db.organization_repositories import OrganizationRepository
from dataall.modules.catalog.db.glossary_repositories import GlossaryRepository
from dataall.modules.datasets_base.services.datasets_enums import DatasetRole
from dataall.modules.redshift_datasets.db.redshift_models import RedshiftDataset
from dataall.modules.redshift_datasets.services.redshift_dataset_service import RedshiftDatasetService

log = logging.getLogger(__name__)


def import_redshift_dataset(context: Context, source, input=None):
    # TODO: validate input

    admin_group = input['SamlAdminGroupName']
    uri = input['environmentUri']
    return RedshiftDatasetService.import_redshift_dataset(uri=uri, admin_group=admin_group, data=input)


def resolve_dataset_organization(context, source: RedshiftDataset, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return OrganizationRepository.get_organization_by_uri(session, source.organizationUri)


def resolve_dataset_environment(context, source: RedshiftDataset, **kwargs): #TODO- duplicated with S3 datasets
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return EnvironmentService.get_environment_by_uri(session, source.environmentUri)


def resolve_dataset_owners_group(context, source: RedshiftDataset, **kwargs): #TODO- duplicated with S3 datasets
    if not source:
        return None
    return source.SamlAdminGroupName


def resolve_dataset_stewards_group(context, source: RedshiftDataset, **kwargs): #TODO- duplicated with S3 datasets
    if not source:
        return None
    return source.stewards


def resolve_user_role(context: Context, source: RedshiftDataset, **kwargs):
    if not source:
        return None
    if source.owner == context.username:
        return DatasetRole.Creator.value
    elif source.SamlAdminGroupName in context.groups:
        return DatasetRole.Admin.value
    elif source.stewards in context.groups:
        return DatasetRole.DataSteward.value
    return DatasetRole.NoPermission.value


def resolve_dataset_glossary_terms(context: Context, source: RedshiftDataset, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return GlossaryRepository.get_glossary_terms_links(session, source.datasetUri, 'RedshiftDataset')

