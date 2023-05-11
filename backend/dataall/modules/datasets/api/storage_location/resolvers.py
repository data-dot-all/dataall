from dataall.api.context import Context
from dataall.db.api import Glossary
from dataall.modules.datasets.services.dataset_location_service import DatasetLocationService
from dataall.modules.datasets_base.db.models import DatasetStorageLocation, Dataset


def create_storage_location(
    context, source, datasetUri: str = None, input: dict = None
):
    return DatasetLocationService.create_storage_location(uri=datasetUri, data=input)


def list_dataset_locations(context, source, filter: dict = None):
    if not source:
        return None
    if not filter:
        filter = {}
    return DatasetLocationService.list_dataset_locations(uri=source.datasetUri, filter=filter)


def get_storage_location(context, source, locationUri=None):
    return DatasetLocationService.get_storage_location(uri=locationUri)


def update_storage_location(
    context, source, locationUri: str = None, input: dict = None
):
    return DatasetLocationService.update_storage_location(uri=locationUri, data=input)


def remove_storage_location(context, source, locationUri: str = None):
    return DatasetLocationService.remove_storage_location(uri=locationUri)


def resolve_dataset(context, source: DatasetStorageLocation, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        d = session.query(Dataset).get(source.datasetUri)
    return d


def publish_location_update(context: Context, source, locationUri: str = None):
    return DatasetLocationService.publish_location_update(uri=locationUri)


def resolve_glossary_terms(
    context: Context, source: DatasetStorageLocation, **kwargs
):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return Glossary.get_glossary_terms_links(
            session, source.locationUri, 'DatasetStorageLocation'
        )
