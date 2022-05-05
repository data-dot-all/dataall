from ....api.context import Context
from ....aws.handlers.s3 import S3
from ....aws.handlers.service_handlers import Worker
from ....db import models, permissions
from ....db.api import (Dataset, DatasetStorageLocation, Environment, Glossary,
                        ResourcePolicy)
from ....searchproxy import indexers


def create_storage_location(context, source, datasetUri: str = None, input: dict = None):
    with context.engine.scoped_session() as session:
        location = DatasetStorageLocation.create_dataset_location(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=datasetUri,
            data=input,
            check_perm=True,
        )

        S3.create_bucket_prefix(location)

        indexers.upsert_folder(session=session, es=context.es, locationUri=location.locationUri)
    return location


def list_dataset_locations(context, source, filter: dict = None):
    if not source:
        return None
    if not filter:
        filter = {}
    with context.engine.scoped_session() as session:
        return DatasetStorageLocation.list_dataset_locations(
            session=session, uri=source.datasetUri, data=filter, check_perm=True
        )


def get_storage_location(context, source, locationUri=None):
    with context.engine.scoped_session() as session:
        location = DatasetStorageLocation.get_location_by_uri(session, locationUri)
        return DatasetStorageLocation.get_dataset_location(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=location.datasetUri,
            data={"locationUri": location.locationUri},
            check_perm=True,
        )


def update_storage_location(context, source, locationUri: str = None, input: dict = None):
    with context.engine.scoped_session() as session:
        location = DatasetStorageLocation.get_location_by_uri(session, locationUri)
        input["location"] = location
        input["locationUri"] = location.locationUri
        DatasetStorageLocation.update_dataset_location(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=location.datasetUri,
            data=input,
            check_perm=True,
        )
        indexers.upsert_folder(session, context.es, location.locationUri)

        return location


def remove_storage_location(context, source, locationUri: str = None):
    with context.engine.scoped_session() as session:
        location = DatasetStorageLocation.get_location_by_uri(session, locationUri)
        DatasetStorageLocation.delete_dataset_location(
            session=session,
            username=context.username,
            groups=context.groups,
            uri=location.datasetUri,
            data={"locationUri": location.locationUri},
            check_perm=True,
        )
        indexers.delete_doc(es=context.es, doc_id=location.locationUri)
    return True


def resolve_dataset(context, source: models.DatasetStorageLocation, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        d = session.query(models.Dataset).get(source.datasetUri)
    return d


def publish_location_update(context: Context, source, locationUri: str = None):
    with context.engine.scoped_session() as session:
        location = DatasetStorageLocation.get_location_by_uri(session, locationUri)
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
                "Subscriptions are disabled. " "First enable subscriptions for this dataset's environment then retry."
            )
        task = models.Task(
            targetUri=location.datasetUri,
            action="sns.dataset.publish_update",
            payload={"s3Prefix": location.S3Prefix},
        )
        session.add(task)

    Worker.process(engine=context.engine, task_ids=[task.taskUri], save_response=False)
    return True


def resolve_glossary_terms(context: Context, source: models.DatasetStorageLocation, **kwargs):
    if not source:
        return None
    with context.engine.scoped_session() as session:
        return Glossary.get_glossary_terms_links(session, source.locationUri, "DatasetStorageLocation")
