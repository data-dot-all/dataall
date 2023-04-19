from dataall.api.context import Context
from dataall.aws.handlers.service_handlers import Worker
from dataall.aws.handlers.s3 import S3
from dataall.db import permissions, models
from dataall.db.api import (
    ResourcePolicy,
    Glossary,
    Dataset,
    Environment,
)
from dataall.modules.datasets.handlers.s3_location_handler import S3DatasetLocationHandler
from dataall.searchproxy import indexers
from dataall.modules.datasets.db.models import DatasetStorageLocation
from dataall.modules.datasets.services.dataset_location import DatasetStorageLocationService
from dataall.searchproxy.indexers import DatasetLocationIndexer


def create_storage_location(
    context, source, datasetUri: str = None, input: dict = None
):
    with context.engine.scoped_session() as session:
        location = DatasetStorageLocationService.create_dataset_location(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=datasetUri,
            data=input,
            check_perm=True,
        )

        S3DatasetLocationHandler.create_bucket_prefix(location)

        DatasetLocationIndexer.upsert(session=session, folder_uri=location.locationUri)
    return location


def list_dataset_locations(context, source, filter: dict = None):
    if not source:
        return None
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return DatasetStorageLocationService.list_dataset_locations(
            session=session, uri=source.datasetUri, data=filter, check_perm=True
        )


def get_storage_location(context, source, locationUri=None):
    with context.engine.scoped_session() as session:
        location = DatasetStorageLocationService.get_location_by_uri(session, locationUri)
        return DatasetStorageLocationService.get_dataset_location(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=location.datasetUri,
            data={'locationUri': location.locationUri},
            check_perm=True,
        )


def update_storage_location(
    context, source, locationUri: str = None, input: dict = None
):
    with context.engine.scoped_session() as session:
        location = DatasetStorageLocationService.get_location_by_uri(session, locationUri)
        input['location'] = location
        input['locationUri'] = location.locationUri
        DatasetStorageLocationService.update_dataset_location(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=location.datasetUri,
            data=input,
            check_perm=True,
        )
        DatasetLocationIndexer.upsert(session, folder_uri=location.locationUri)

        return location


def remove_storage_location(context, source, locationUri: str = None):
    with context.engine.scoped_session() as session:
        location = DatasetStorageLocationService.get_location_by_uri(session, locationUri)
        DatasetStorageLocationService.delete_dataset_location(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=location.datasetUri,
            data={'locationUri': location.locationUri},
            check_perm=True,
        )
        indexers.delete_doc(es=context.es, doc_id=location.locationUri)
    return True


def resolve_dataset(context, source: DatasetStorageLocation, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        d = session.query(models.Dataset).get(source.datasetUri)
    return d


def publish_location_update(context: Context, source, locationUri: str = None):
    with context.engine.scoped_session() as session:
        location = DatasetStorageLocationService.get_location_by_uri(session, locationUri)
        ResourcePolicy.check_user_resource_permission(
            session=session,
            username=context.username,
            groups=context.groups,
            resource_uri=location.datasetUri,
            permission_name=permissions.UPDATE_DATASET_FOLDER,
        )
        dataset = Dataset.get_dataset_by_uri(session, location.datasetUri)
        env = Environment.get_environment_by_uri(session, dataset.environmentUri)
        if not env.subscriptionsEnabled or not env.subscriptionsProducersTopicName:
            raise Exception(
                'Subscriptions are disabled. '
                "First enable subscriptions for this dataset's environment then retry."
            )
        task = models.Task(
            targetUri=location.datasetUri,
            action='sns.dataset.publish_update',
            payload={'s3Prefix': location.S3Prefix},
        )
        session.add(task)

    Worker.process(engine=context.engine, task_ids=[task.taskUri], save_response=False)
    return True


def resolve_glossary_terms(
    context: Context, source: DatasetStorageLocation, **kwargs
):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return Glossary.get_glossary_terms_links(
            session, source.locationUri, 'DatasetStorageLocation'
        )
