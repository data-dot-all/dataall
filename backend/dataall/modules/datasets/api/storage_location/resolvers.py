from dataall.base.api.context import Context
from dataall.modules.catalog.db.glossary_repositories import GlossaryRepository
from dataall.base.db.exceptions import RequiredParameter
from dataall.core.feature_toggle_checker import is_feature_enabled
from dataall.modules.datasets.services.dataset_location_service import DatasetLocationService
from dataall.modules.datasets_base.db.dataset_models import DatasetStorageLocation, Dataset


@is_feature_enabled('modules.datasets.features.file_actions')
def create_storage_location(
    context, source, datasetUri: str = None, input: dict = None
):
    if 'prefix' not in input:
        raise RequiredParameter('prefix')
    if 'label' not in input:
        raise RequiredParameter('label')

    return DatasetLocationService.create_storage_location(uri=datasetUri, data=input)


@is_feature_enabled('modules.datasets.features.file_actions')
def list_dataset_locations(context, source, filter: dict = None):
    if not source:
        return None
    if not filter:
        filter = {}
    return DatasetLocationService.list_dataset_locations(uri=source.datasetUri, filter=filter)


@is_feature_enabled('modules.datasets.features.file_actions')
def get_storage_location(context, source, locationUri=None):
    return DatasetLocationService.get_storage_location(uri=locationUri)


@is_feature_enabled('modules.datasets.features.file_actions')
def update_storage_location(
    context, source, locationUri: str = None, input: dict = None
):
    return DatasetLocationService.update_storage_location(uri=locationUri, data=input)


@is_feature_enabled('modules.datasets.features.file_actions')
def remove_storage_location(context, source, locationUri: str = None):
    return DatasetLocationService.remove_storage_location(uri=locationUri)


def resolve_dataset(context, source: DatasetStorageLocation, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        d = session.query(Dataset).get(source.datasetUri)
    return d


def resolve_glossary_terms(
    context: Context, source: DatasetStorageLocation, **kwargs
):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return GlossaryRepository.get_glossary_terms_links(
            session, source.locationUri, 'DatasetStorageLocation'
        )
