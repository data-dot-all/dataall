from dataall.base.api.context import Context
from dataall.base.db.exceptions import RequiredParameter
from dataall.base.feature_toggle_checker import is_feature_enabled
from dataall.modules.catalog.db.glossary_repositories import GlossaryRepository
from dataall.modules.s3_datasets.db.dataset_models import DatasetStorageLocation
from dataall.modules.s3_datasets.services.dataset_location_service import DatasetLocationService
from dataall.modules.s3_datasets.services.dataset_service import DatasetService


def _validate_input(input: dict):
    if 'label' not in input:
        raise RequiredParameter('label')
    if 'prefix' not in input:
        raise RequiredParameter('prefix')


@is_feature_enabled('modules.s3_datasets.features.file_actions')
def create_storage_location(context, source, datasetUri: str = None, input: dict = None):
    _validate_input(input)
    return DatasetLocationService.create_storage_location(uri=datasetUri, data=input)


@is_feature_enabled('modules.s3_datasets.features.file_actions')
def list_dataset_locations(context, source, filter: dict = None):
    if not source:
        return None
    if not filter:
        filter = {}
    return DatasetLocationService.list_dataset_locations(uri=source.datasetUri, filter=filter)


@is_feature_enabled('modules.s3_datasets.features.file_actions')
def get_storage_location(context, source, locationUri=None):
    return DatasetLocationService.get_storage_location(uri=locationUri)


@is_feature_enabled('modules.s3_datasets.features.file_actions')
def update_storage_location(context, source, locationUri: str = None, input: dict = None):
    return DatasetLocationService.update_storage_location(uri=locationUri, data=input)


@is_feature_enabled('modules.s3_datasets.features.file_actions')
def remove_storage_location(context, source, locationUri: str = None):
    return DatasetLocationService.remove_storage_location(uri=locationUri)


def resolve_dataset(context, source: DatasetStorageLocation, **kwargs):
    if not source:
        return None
    return DatasetService.find_dataset(uri=source.datasetUri)


def get_folder_restricted_information(context: Context, source: DatasetStorageLocation, **kwargs):
    if not source:
        return None
    return DatasetLocationService.get_folder_restricted_information(uri=source.locationUri, folder=source)


def resolve_glossary_terms(context: Context, source: DatasetStorageLocation, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return GlossaryRepository.get_glossary_terms_links(session, source.locationUri, 'Folder')
